======
gcpdns
======

A Python module and CLI for managing resource records on Google Cloud DNS

::

    gcpdns: A CLI for managing resource records on Google Cloud DNS

    Usage:
      gcpdns <credential_file> zones [-f csv|json] [-o <output_file>]...
      gcpdns <credential_file> records <zone> [-f csv|json] [-o <output_file>]...
      gcpdns <credential_file> apply [--verbose] [--ignore-errors]
      [--error-on-existing] <csv_file>
      gcpdns -h | --help
      gcpdns --version

    Options:
      -h --help            Show this screen.
      --version            Show version.
      -f                   Set the screen output format [default: json].
      -o                   Output to these files and suppress screen output.
      --verbose            Enable verbose logging output.
      --ignore-errors      Do not stop processing when an error occurs
      --error-on-existing  When an existing record set is found, raise an
      error instead of replacing it.

Features
--------

- Dump all project zones or zone resource records in CSV or JSON format
- Update DNS resource records for multiple zones in one project using one CSV
  file

Setup
-----

To use ``gcpdns``, you'll need a separate `service account`_ credentials JSON
file for each project that you want to work with.

Ensure that the Service Account has the proper permissions to edit DNS
(e.g. the DNS Administrator role) in the project.

Records CSV fields
------------------

- ``action`` - ``add`` or ``remove``
- ``name`` - The record set name (i.e. the Fully-Qualified Domain Name)
- ``record_type`` - The DNS record type
- ``ttl`` - DNS time to live (in seconds)
- ``data`` - DNS record data separated by ``|``

.. _service account: https://cloud.google.com/iam/docs/creating-managing-service-accounts
