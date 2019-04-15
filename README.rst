======
gcpdns
======

A Python module and CLI for managing resource records on Google Cloud DNS

::

    gcpdns: A CLI for managing resource records on Google Cloud DNS

    Usage:
      gcpdns <credential_file> zones [-f csv|json] [-o <output_file>]...
      gcpdns <credential_file> records <zone> [-f csv|json] [-o <output_file>]...
      gcpdns <credential_file> apply [--verbose] [--ignore-errors] <csv_file>
      gcpdns -h | --help
      gcpdns --version

    Options:
      -h --help            Show this screen.
      --version            Show version.
      -f                   Set the screen output format [default: json].
      -o                   Output to these files and suppress screen output.
      --verbose            Enable verbose logging output.
      --ignore-errors      Do not stop processing when an error occurs.

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

- ``action``

  - ``add`` - Adds a resource record set
  - ``replace`` - The same as ``add``, but will replace an existing resource
    record set with the same ``name`` and ``record_type`` (if it exists)
  - ``delete`` - Deletes a resource record set

- ``name`` - The record set name (i.e. the Fully-Qualified Domain Name)
- ``record_type`` - The DNS record type
- ``ttl`` - DNS time to live (in seconds)
- ``data`` - DNS record data separated by ``|``

.. _service account: https://cloud.google.com/iam/docs/creating-managing-service-accounts
