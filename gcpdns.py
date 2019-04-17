#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""A Python module and CLI for managing resource records on
Google Cloud DNS"""

from __future__ import absolute_import, print_function, unicode_literals

import logging
import csv
import json
import collections
import io
import textwrap

from google.oauth2 import service_account
from google.cloud import dns
import publicsuffix2
import docopt

__version__ = "1.1.2"

ZONE_CACHE = dict()

logger = logging.getLogger(__name__)


class ZoneNotFound(ValueError):
    """Raised when a requested zone is not found"""


class ZoneConflict(ValueError):
    """Raised when a conflicting zone already exists"""


class RecordSetNotFound(ValueError):
    """Raised when a record set is not found"""


class ExistingRecordSetFound(ValueError):
    """Raised when an existing record set is found"""


class CSVError(ValueError):
    """Raised when a CSV parsing error occurs"""


class DNSClient(dns.Client):
    """An extended Google DNS client with helper functions"""
    def get_zone(self, name):
        """
        Get a Zone object by zone name or DNS name

        Args:
            name (str): zone name or dns_name

        Raises:
            gcpclient.ZoneNotFound
        """
        dns_name = "{0}.".format(name.lower().rstrip("."))
        zones = self.list_zones()
        for zone in zones:
            if zone.name == name or zone.dns_name == dns_name:
                return zone
        raise ZoneNotFound("The zone named {0} was not found".format(name))

    def create_zone(self, dns_name, name=None, description=None):
        """
        Creates a DNS zone

        Args:
            dns_name (str): The zone's DNS name
            name (str): the zone's GCP name
            description (str): A description of the zone

        Raises:
            gcpclient.ZoneConflict
        """
        dns_name = dns_name.lower()
        if name is None:
            name = dns_name.replace(".", "-")
        zones = self.list_zones()
        for zone in zones:
            if zone.name == name or zone.dns_name == dns_name:
                raise ZoneConflict(
                    "A conflicting zone already exists: {0} ({1})".format(
                        zone.dns_name, zone.name
                    ))
        self.zone(name, dns_name=dns_name, description=description).create()

    def delete_zone(self, zone_name):
        """
        Deletes a zone

        Args:
            zone_name: The zone's DNS name of GCP name

        Returns:

        """
        self.get_zone(zone_name).delete()

    def dump_zones(self):
        """
        Outputs all managed zones  for the project in JASON and CSV format

        Returns:
            dict: A dictionary with a csv and json key
        """
        zones = []
        for zone in self.list_zones():
            zone_dict = collections.OrderedDict(
                dns_name=zone.dns_name,
                name=zone.name,
                created=zone.created.isoformat(),
                description=zone.description,
                name_servers=zone.name_servers)
            zones.append(zone_dict)
        _json = json.dumps(zones, indent=2, ensure_ascii=False)
        csv_str = io.StringIO()
        csv_fields = ["dns_name", "name", "created",
                      "description", "name_servers"]
        csv_rows = zones.copy()
        for zone in csv_rows:
            zone["name_servers"] = "|".join(zone["name_servers"])
        csv_writer = csv.DictWriter(csv_str, fieldnames=csv_fields)
        csv_writer.writeheader()
        csv_writer.writerows(csv_rows)
        _csv = csv_str.getvalue()

        return dict(csv=_csv, json=_json)

    def dump_records(self, zone_name):
        """
        Outputs all record sets for a given zone in JASON and CSV format

        Args:
            zone_name (str): The zone name or DNS name

        Returns:
            dict: A dictionary with a csv and json key
        """
        zone = self.get_zone(zone_name)
        records = []
        for record in zone.list_resource_record_sets():
            record_dict = collections.OrderedDict(
                name=record.name,
                record_type=record.record_type,
                ttl=record.ttl,
                data=record.rrdatas
            )
            records.append(record_dict)

        _json = json.dumps(records, indent=2, ensure_ascii=False)
        csv_str = io.StringIO()
        csv_fields = ["name", "record_type", "ttl", "data"]
        csv_rows = records.copy()
        for zone in csv_rows:
            zone["data"] = "|".join(zone["data"])
        csv_writer = csv.DictWriter(csv_str, fieldnames=csv_fields)
        csv_writer.writeheader()
        csv_writer.writerows(csv_rows)
        _csv = csv_str.getvalue()

        return dict(csv=_csv, json=_json)

    def create_or_replace_record_set(self, name, record_type, data, ttl=300,
                                     replace=False):
        """
        Adds or replaces a DNS resource record set

        Args:
            name (str): The DNS name (i.e. the fully-qualified domain name)
            record_type (str): The DNS record type
            data: A list of resource record data strings,
            or a string of one or more resource records separated by |
            ttl (int): Time to live (in seconds)
            replace (bool): Replace existing record set if needed

        Raises:
            gcpdns.ExistingRecordSetFound
        """
        tld = publicsuffix2.get_public_suffix(name).lower()
        if tld in ZONE_CACHE:
            zone = ZONE_CACHE[tld]
        else:
            zone = self.get_zone(tld)
            ZONE_CACHE[tld] = zone
        name = "{0}{1}".format(
            name.lower().rstrip(".").replace(zone.dns_name.rstrip("."), ""),
            zone.dns_name).lstrip(".")
        record_type = record_type.upper()
        if ttl is None:
            ttl = 300
        ttl = int(ttl)
        old_record_set = None
        change = zone.changes()
        for r_set in zone.list_resource_record_sets():
            if r_set.name == name and r_set.record_type == record_type:
                old_record_set = r_set
                if not replace:
                    raise ExistingRecordSetFound(
                        "Existing record set found: {0} {1} {2} {3}".format(
                            r_set.name,
                            r_set.record_type,
                            r_set.ttl,
                            r_set.rrdata
                        ))
                change.delete_record_set(r_set)
        if type(data) == str:
            if record_type == "CNAME":
                data = "{0}.".format(data.rstrip("."))
                data = [data]
            elif record_type == "TXT":
                new_data = []
                data = data.split("|")
                for r_set in data:
                    r_set = r_set.strip('"')
                    split_records = textwrap.wrap(r_set, 253)
                    for split_record in split_records:
                        split_record = '"{0}"'.format(split_record)
                        new_data.append(split_record)
                data = new_data.copy()
            else:
                data = data.split("|")
        if record_type in ["CNAME", "MX", "NS", "PTR", "SRV"]:
            for i in range(len(data)):
                data[i] = "{0}.".format(data[i].rstrip("."))
        if old_record_set is None:
            logging.debug(
                "Adding record set: {0} {1} {2} {3}".format(
                    name,
                    record_type,
                    ttl,
                    data
                ))
        else:
            logging.debug(
                "Replacing record set: {0} {1} {2} {3} "
                "with: {4} {5} {6} {7}".format(
                    old_record_set.name,
                    old_record_set.record_type,
                    old_record_set.ttl,
                    old_record_set.rrdatas,
                    name,
                    record_type,
                    ttl,
                    data
                ))
        r_set = zone.resource_record_set(name, record_type, ttl, rrdatas=data)
        change.add_record_set(r_set)
        change.create()

    def delete_record_set(self, name, record_type):
        """
        Deletes a record set

        Args:
            name (str): The DNS name (i.e. the fully-qualified domain name)
            record_type (str): The DNS record type

        Raises:
            gcpdns.RecordSetDoesNotExist
        """
        logger.info("Deleting record set: {0} {1}".format(name, record_type))
        tld = publicsuffix2.get_public_suffix(name).lower()
        if tld in ZONE_CACHE:
            zone = ZONE_CACHE[tld]
        else:
            zone = self.get_zone(tld)
            ZONE_CACHE[tld] = zone
        name = "{0}{1}".format(
            name.lower().rstrip(".").replace(zone.dns_name.rstrip("."), ""),
            zone.dns_name).lstrip(".")
        record_type = record_type.upper()
        record_to_delete = None
        change = zone.changes()
        records = zone.list_resource_record_sets()
        for record in records:
            if record.name == name and record.record_type == record_type:
                record_to_delete = record
        if record_to_delete is not None:
            change.delete_record_set(record_to_delete)
            change.create()
        else:
            raise RecordSetNotFound(
                "Record set not found: {0} {1}".format(name,
                                                       record_type))

    def apply_zones_csv(self, csv_file, ignore_errors=False):
        """
        Apply a CSV of zones

        The CSV fields are:
        - ``action``

            - ``create`` - Creates a zone
            - ``delete`` - Deletes a zone

        - ``dns_name`` - The zone's DNS name
        - ``gcp_name`` - The zone's name in GCP (optional)
        - ``description`` - DNS time to live (in seconds)

        Args:
            csv_file: A file or file-like object
            ignore_errors (bool): Log errors instead of raising an exception

        Raises:
            gcpdns.CSVError
        """
        logger.info("Applying zones CSV")
        reader = csv.DictReader(csv_file)
        for row in reader:
            try:
                dns_name = row["dns_name"].lower()
                action = row["action"].lower()
            except KeyError as e:
                error = "Line {0}: Missing {1)".format(reader.line_num,
                                                       e.__str__())
                if ignore_errors:
                    logger.error(error)
                    continue
                else:
                    raise CSVError(error)

            gcp_name = None
            if "gcp_name" in row:
                gcp_name = row["gcp_name"]
            description = None
            if "description" in row:
                description = row["description"]
            if action == "delete":
                try:
                    self.delete_zone(dns_name)
                except ZoneNotFound as e:
                    error = "Line {0}: {1}".format(reader.line_num,
                                                   e.__str__())
                    if ignore_errors:
                        logger.warning(error)
                    else:
                        raise CSVError(error)

            elif action == "create":
                try:
                    self.create_zone(dns_name=dns_name, name=gcp_name,
                                     description=description)
                except ZoneConflict as e:
                    error = "Line {0}: {1}".format(reader.line_num,
                                                   e.__str__())
                    if ignore_errors:
                        logger.error(error)
                    else:
                        raise CSVError(error)

            else:
                error = "Line {0}: Invalid action".format(
                    reader.line_num)
                if ignore_errors:
                    logger.error(error)
                else:
                    raise CSVError(error)

    def apply_record_sets_csv(self, csv_file, ignore_errors=False):
        """
        Apply a CSV of record set changes

        The CSV fields are:
        - ``action``

            - ``create`` - Creates a resource record set
            - ``replace`` - The same as ``create``, but will replace an
            existing resource record set with the same ``name`` and `
            `record_type``(if it exists)
            - ``delete`` - Deletes a resource record set

        - ``name`` - The record set name (i.e. the Fully-Qualified Domain Name)
        - ``record_type`` - The DNS record type
        - ``ttl`` - DNS time to live (in seconds)
        - ``data`` - DNS record data separated by ``|``

        Args:
            csv_file: A file or file-like object
            ignore_errors (bool): Log errors instead of raising an exception

        Raises:
            gcpdns.CSVError
        """
        logger.info("Applying record sets CSV")
        reader = csv.DictReader(csv_file)
        for row in reader:
            try:
                name = row["name"].lower()
                action = row["action"].lower()
                record_type = row["type"].upper()
            except KeyError as e:
                error = "Line {0}: Missing {1)".format(reader.line_num,
                                                       e.__str__())
                if ignore_errors:
                    logger.error(error)
                    continue
                else:
                    raise CSVError(error)
            ttl = None
            if "ttl" in row:
                ttl = int(row["ttl"])
            data = None
            if "data" in row:
                data = row["data"]
            if action == "delete":
                try:
                    self.delete_record_set(name, record_type)
                except RecordSetNotFound as e:
                    error = "Line {0}: {1}".format(reader.line_num,
                                                   e.__str__())
                    if ignore_errors:
                        logger.warning(error)
                    else:
                        raise CSVError(error)

            elif action in ["create", "replace"]:
                if data is not None:
                    replace = action == "replace"
                    try:
                        self.create_or_replace_record_set(
                            name, record_type,
                            data, ttl=ttl, replace=replace)
                    except ExistingRecordSetFound as e:
                        error = "Line {0}: {1}".format(reader.line_num,
                                                       e.__str__())
                        if ignore_errors:
                            logger.error(error)
                        else:
                            raise CSVError(error)
                else:
                    error = "Line {0}: Missing data".format(
                        reader.line_num)
                    if ignore_errors:
                        logger.error(error)
                    else:
                        raise CSVError(error)

            else:
                error = "Line {0}: Invalid action".format(
                    reader.line_num)
                if ignore_errors:
                    logger.error(error)
                else:
                    raise CSVError(error)


def _main():
    usage = """
    gcpdns: A CLI for managing resource records on Google Cloud DNS
    
    Usage:
      gcpdns <credential_file> zone dump [-f csv|json] [-o <output_file>]...
      gcpdns <credential_file> zone create <dns_name> [<gcp_name>]
      gcpdns <credential_file> zone delete [-y | --yes] <zone_name>
      gcpdns <credential_file> zone apply [--verbose] [--ignore-errors] <csv_file>
      gcpdns <credential_file> record dump <zone> [-f csv|json] [-o <output_file>]...
      gcpdns <credential_file> record create <name> <record_type> [--ttl=<seconds>] <data>
      gcpdns <credential_file> record replace <name> <record_type> [--ttl=<seconds>] <data>
      gcpdns <credential_file> record delete <name> <record_type>
      gcpdns <credential_file> record apply [--verbose] [--ignore-errors] <csv_file>
      gcpdns -h | --help
      gcpdns --version
    
    Options:
      -h --help            Show this screen.
      --version            Show version.
      -y --yes             Skip action confirmation.
      -f                   Set the screen output format [default: json].
      -o                   Output to these files and suppress screen output.
      --ttl=<seconds>      DNS time to live in seconds [default: 300]
      --verbose            Enable verbose logging output.
      --ignore-errors      Do not stop processing when an error occurs.
  """
    args = docopt.docopt(usage, version=__version__)
    if args["--verbose"]:
        logging.basicConfig(level=logging.INFO,
                            format="%(levelname)s: %(message)s")
    else:
        logging.basicConfig(level=logging.WARNING,
                            format="%(levelname)s: %(message)s")

    scopes = ['https://www.googleapis.com/auth/cloud-platform',
              'https://www.googleapis.com/auth/ndev.clouddns.readwrite']
    credentials = service_account.Credentials.from_service_account_file(
        args["<credential_file>"], scopes=scopes)
    client = DNSClient(credentials=credentials,
                       project=credentials.project_id)

    if args["record"] and args["apply"]:
        with open(args["<csv_file>"], encoding="utf-8",
                  errors="ignore") as csv_file:
            try:
                client.apply_record_sets_csv(
                    csv_file,
                    ignore_errors=args["--ignore-errors"]
                )
            except Exception as e:
                logger.error(e.__str__())
                exit(-1)
    elif args["zone"] and args["dump"]:
        zones = []
        try:
            zones = client.dump_zones()
        except Exception as e:
            logger.error(e.__str__())
            exit(-1)
        if len(args["<output_file>"]) == 0:
            if args["csv"]:
                print(zones["csv"])
            else:
                print(zones["json"])
        for file_path in args["<output_file>"]:
            if file_path.lower().endswith("json"):
                with open(file_path,
                          "w", encoding="utf-8",
                          newline="\n",
                          errors="ignore") as output_file:
                    output_file.write(zones["json"])
            elif file_path.lower().endswith(".csv"):
                with open(file_path,
                          "w", encoding="utf-8",
                          newline="\n",
                          errors="ignore") as output_file:
                    output_file.write(zones["csv"])
            else:
                logger.error("Output filenames must end in .csv or .json")
                exit(-1)

    elif args["record"] and args["dump"]:
        records = []
        try:
            records = client.dump_records(args["<zone>"])
        except Exception as e:
            logger.error(e.__str__())
            exit(-1)
        if len(args["<output_file>"]) == 0:
            if args["csv"]:
                print(records["csv"])
            else:
                print(records["json"])
        for file_path in args["<output_file>"]:
            if file_path.lower().endswith("json"):
                with open(file_path,
                          "w", encoding="utf-8",
                          newline="\n",
                          errors="ignore") as output_file:
                    output_file.write(records["json"])
            elif file_path.lower().endswith(".csv"):
                with open(file_path,
                          "w", encoding="utf-8",
                          newline="\n",
                          errors="ignore") as output_file:
                    output_file.write(records["csv"])
            else:
                logger.error("Output filenames must end in .csv or .json")
                exit(-1)
    elif args["zone"] and args["add"]:
        client.create_zone()


if __name__ == "__main__":
    _main()
