======
gcpdns
======

A Python module and CLI for managing zones and resource record sets on Google Cloud DNS

Features
--------

- Dump all project zones names in CSV and/or JSON format
- Dump all zone resource record sets in CSV and/or JSON format
- Create and delete zones via CLI or CSV
- Create and delete resource record sets via CLI
- Update DNS resource records for multiple zones in one project using one CSV
  file
- Automatically split ``TXT`` records longer than 255 characters when publishing
- Automatically add an ending ``.`` to records when needed

CLI
---

::

    Usage: gcpdns [OPTIONS] CREDENTIAL_FILE COMMAND [ARGS]...

      gcpdns: A CLI for managing zones and resource record sets on Google Cloud
      DNS.

    Options:
      --version  Show the version and exit.
      --verbose  Enable verbose logging.
      --help     Show this message and exit.

    Commands:
      record  Manage DNS resource record sets.
      zone    Manage DNS zones.


gcpdns record
~~~~~~~~~~~~~

::

    Usage: gcpdns record [OPTIONS] COMMAND [ARGS]...

      Manage DNS resource record sets.

    Options:
      --help  Show this message and exit.

    Commands:
      create  Create a resource record set (Data fields separated by |).
      delete  Delete a resource record set
      dump    Dump a list of DNS resource records.
      update  Create, replace, and delete resource record sets using a CSV file.

gcpdns record create
````````````````````

::

    Usage: gcpdns record create [OPTIONS] NAME RECORD_TYPE DATA

      Create a resource record set (Data fields separated by |).

    Options:
      -r, --replace      Replace any conflicting resource record set
      -t, --ttl seconds  DNS Time to live (in seconds)  [default: 300]
      --help             Show this message and exit.

gcpdns record delete
````````````````````

::

    Usage: gcpdns record delete [OPTIONS] NAME RECORD_TYPE

      Delete a resource record set

    Options:
      --yes   Confirm the action without prompting.
      --help  Show this message and exit.


gcpdns record dump
``````````````````

::

    Usage: gcpdns record dump [OPTIONS] ZONE

      Dump a list of DNS resource records.

    Options:
      -f, --format [json|csv]  Set the screen output format  [default: json]
      -o, --output FILE        One or more output file paths that end in .csv or
                               .json (suppresses screen output).
      --help                   Show this message and exit.

gcpdns record update
````````````````````

::

    Usage: gcpdns record update [OPTIONS] CSV_FILE_PATH

      Create, replace, and delete resource record sets using a CSV file.

    Options:
      --ignore-errors  Continue processing the CSV when errors occur.
      --help           Show this message and exit.


gcpdns zone
~~~~~~~~~~~

::

    Manage DNS zones.

    Options:
      --help  Show this message and exit.

    Commands:
      create  Create a DNS zone.
      delete  Delete a DNS zone and all its resource records.
      dump    Dump a list of DNS zones.
      update  Create and delete zones using a CSV file.


gcpdns zone create
``````````````````

::

    Usage: gcpdns zone create [OPTIONS] DNS_NAME

      Create a DNS zone.

    Options:
      --gcp_name TEXT     Set the zone's GCP name.
      --description TEXT  Set the zone's description.
      --help              Show this message and exit.

gcpdns zone delete
``````````````````

::

    Usage: gcpdns zone delete [OPTIONS] NAME

      Delete a DNS zone and all its resource records.

    Options:
      --yes   Confirm the action without prompting.
      --help  Show this message and exit.


gcpdns zone dump
````````````````

::

    Usage: gcpdns zone dump [OPTIONS]

      Dump a list of DNS zones.

    Options:
      -f, --format [json|csv]  Set the screen output format  [default: json]
      -o, --output FILE        One or more output file paths that end in .csv or
                               .json (suppresses screen output).
      --help                   Show this message and exit.

gcpdns zone update
``````````````````

::

    Usage: gcpdns zone update [OPTIONS] CSV_FILE_PATH

      Create and delete zones using a CSV file.

    Options:
      --ignore-errors  Continue processing the CSV when errors occur.
      --help           Show this message and exit.


Installation
------------

Use ``pip`` (or ``pip3`` for Python 3)

::

    sudo -H pip install gcpdns

Setup
-----

To use ``gcpdns``, you'll need a separate `service account`_ credentials JSON
file for each GCP project that you want to work with.

Ensure that the Service Account has the proper permissions to edit DNS
(e.g. the DNS Administrator role) in the project.

Zone CSV fields
---------------

- ``action``

  - ``create`` - Creates a zone
  - ``delete`` - Deletes a zone

- ``dns_name``    - The zone's DNS name
- ``gcp_name``    - The zone's name in GCP (optional)
- ``description`` - The zone's description (optional)



Record CSV fields
-----------------

- ``action``

  - ``create`` - Creates a resource record set
  - ``replace`` - The same as ``create``, but will replace an existing resource
    record set with the same ``name`` and ``record_type`` (if it exists)
  - ``delete`` - Deletes a resource record set

- ``name`` - The record set name (i.e. the Fully-Qualified Domain Name)
- ``record_type`` - The DNS record type
- ``ttl`` - DNS time to live (in seconds)
- ``data`` - DNS record data separated by ``|``

Python API
----------

.. automodule:: gcpdns
   :members:

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. _service account: https://cloud.google.com/iam/docs/creating-managing-service-accounts
