SlapOS Master REST API (v1)
***************************

Find your SSL keys
------------------

You can find  X509 key/certificate to authenticate to the SlapOS Master.
Visit https://www.vifib.net/.

Exchange format
---------------

SlapOS master will support both XML and JSON formats for input and output.

The Accept header is required and responsible for format selection.

Response status code
--------------------

Success
+++++++

``GET`` requests will return a ``"200 OK"`` response if the resource is successfully retrieved.

``POST`` requests which create a resource we will return a ``"201 Created"`` response if successful.

``POST`` requests which perform some other action such as sending a campaign
will return a ``"200 OK"`` response if successful.

``PUT`` requests will return a ``"200 OK"`` response if the resource is successfully updated and ``"204 No Content"`` in case if no modification was applied..

``DELETE`` requests will return a ``"200 OK"`` response if the resource is successfully deleted.

``OPTIONS`` requests will return ``"200 OK"`` response with allowed method on given url.

Common Error Responses
++++++++++++++++++++++

400 Bad Request
~~~~~~~~~~~~~~~
The request body does not follow the API (one argument is missing or malformed). The full information is available as text body::

  HTTP/1.1 400 Bad Request
  Content-Type: application/json

  {
    "computer_id": "Parameter is missing"
  }

402 Payment Required
~~~~~~~~~~~~~~~~~~~~

The request can not be fulfilled because account is locked.

403 Forbidden
~~~~~~~~~~~~~
Wrong SSL key used or access to invalid ID.

404 Not Found
~~~~~~~~~~~~~
Request to non existing resource made.

500 Internal Server Error
~~~~~~~~~~~~~~~~~~~~~~~~~
Unexpected error.

Instance Methods
****************

Requesting a new instance
-------------------------

Request a new instantiation of a software.

`Request`::

  POST http://example.com/api/v1/instance HTTP/1.1
  Accept: application/json
  Content-Type: application/json; charset=utf-8

`Expected Request Body`::

  {
    "title": "My unique instance",
    "software_release": "http://example.com/example.cfg",
    "software_type": "type_provided_by_the_software",
    "slave": False, # one of: True or False
    "status": "started", # one of: started, stopped
    "parameter": {
      "Custom1": "one string",
      "Custom2": "one float",
      "Custom3": ["abc", "def"],
      },
    "sla": {
      "computer_id": "COMP-0",
      }
  }

`Expected Response`::

  HTTP/1.1 201 Created
  Content-Type: application/json; charset=utf-8
  Location: http://maybeother.example.com/some/url/instance_id

  {
    "status": "started",
    "connection": {
      "custom_connection_parameter_1": "foo",
      "custom_connection_parameter_2": "bar"
    }
  }

`Additional Responses`::

  HTTP/1.1 202 Accepted
  Content-Type: application/json; charset=utf-8
  Location: http://maybeother.example.com/some/url/instance_id

  {
    "status": "processing"
  }

The request has been accepted for processing

`Error Responses`:

* ``409 Conflict`` The request can not be process because of the current status of the instance (sla changed, instance is under deletion, software release can not be changed, ...).


Get instance information
------------------------

Request all instance information.

`Request`::

  GET http://example.com/api/v1/instance/{instance_id} HTTP/1.1
  Accept: application/json

`Route values`:

* ``instance_id``: the ID of the instance

`No Expected Request Body`

`Expected Response`::

  HTTP/1.1 200 OK
  Content-Type: application/json; charset=utf-8

  {
    "title": "The Instance Title",
    "status": "start", # one of: start, stop, destroy
    "software_release": "http://example.com/example.cfg",
    "software_type": "type_provided_by_the_software",
    "slave": False, # one of: True, False
    "connection": {
      "custom_connection_parameter_1": "foo",
      "custom_connection_parameter_2": "bar"
    },
    "parameter": {
      "Custom1": "one string",
      "Custom2": "one float",
      "Custom3": ["abc", "def"],
      },
    "sla": {
      "computer_id": "COMP-0",
      }
    "children_id_list": ["subinstance1", "subinstance2"],
    "partition": {
      "public_ip": ["::1", "91.121.63.94"],
      "private_ip": ["127.0.0.1"],
      "tap_interface": "tap2",
    },
  }

`Error Responses`:

* ``409 Conflict`` The request can not be process because of the current status of the instance

Get instance authentication certificates
----------------------------------------

Request the instance certificates.

`Request`::

  GET http://example.com/api/v1/instance/{instance_id}/certificate HTTP/1.1
  Accept: application/json

`Route values`:

* ``instance_id``: the ID of the instance

`No Expected Request Body`

`Expected Response`::

  HTTP/1.1 200 OK
  Content-Type: application/json; charset=utf-8

  {
    "ssl_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADAN...h2VSZRlSN\n-----END PRIVATE KEY-----",
    "ssl_certificate": "-----BEGIN CERTIFICATE-----\nMIIEAzCCAuugAwIBAgICHQI...ulYdXJabLOeCOA=\n-----END CERTIFICATE-----",
  }

`Error Responses`:

* ``409 Conflict`` The request can not be process because of the current status of the instance

Bang instance
-------------

Trigger the re-instantiation of all partitions in the instance tree

`Request`::

  POST http://example.com/api/v1/instance/{instance_id}/bang HTTP/1.1
  Accept: application/json
  Content-Type: application/json; charset=utf-8

`Route values`:

* ``instance_id``: the ID of the instance

`Expected Request Body`::

  {
    "log": "Explain why this method was called",
  }

`Expected Response`::

  HTTP/1.1 200 OK
  Content-Type: application/json; charset=utf-8

Modifying instance
------------------

Modify the instance information and status.

`Request`::

  PUT http://example.com/api/v1/instance/{instance_id} HTTP/1.1
  Accept: application/json
  Content-Type: application/json; charset=utf-8

`Expected Request Body`::

  {
    "title": "The New Instance Title",
    "status": "started", # one of: started, stopped, updating, error
    "log": "explanation of the status",
    "connection": {
      "custom_connection_parameter_1": "foo",
      "custom_connection_parameter_2": "bar"
    }
  }

Where `status` is required with `log`, `connection` and `title` are optional and their existence allow to not send `status` and `log`.

Setting different.

`Expected Response`::

  HTTP/1.1 200 OK
  Content-Type: application/json; charset=utf-8

  {
    'action': ['Action description', 'Action description', ...]
  }

Where `action` describes what happened:

 * 'Renamed' (where title was different)
 * 'Updated status' (where status changed)
 * 'Updated connection information' (where connection changed)

`Additional Responses`::

  HTTP/1.1 204 No Content

When nothing was modified.

`Error Responses`:

* ``409 Conflict`` The request can not be process because of the current status of the instance (sla changed, instance is under deletion, software release can not be changed, ...).

Computer Methods
****************

Registering a new computer
--------------------------

Add a new computer in the system.

`Request`::

  POST http://example.com/api/v1/computer HTTP/1.1
  Accept: application/json
  Content-Type: application/json; charset=utf-8

`Expected Request Body`::

  {
    "title": "My unique computer",
  }

`Expected Response`::

  HTTP/1.1 201 Created
  Content-Type: application/json; charset=utf-8
  Location: http://maybeother.example.com/some/url/computer_id-0

  {
    "ssl_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADAN...h2VSZRlSN\n-----END PRIVATE KEY-----",
    "ssl_certificate": "-----BEGIN CERTIFICATE-----\nMIIEAzCCAuugAwIBAgICHQI...ulYdXJabLOeCOA=\n-----END CERTIFICATE-----",
  }

`Error Responses`:

* ``409 Conflict`` The request can not be process because of the existence of a computer with the same title

Getting computer information
----------------------------

Get the status of a computer

`Request`::

  GET http://example.com/api/v1/computer/{computer_id} HTTP/1.1
  Accept: application/json

`Route values`:

* ``computer_id``: the ID of the computer

`No Expected Request Body`

`Expected Response`::

  HTTP/1.1 200 OK
  Content-Type: application/json; charset=utf-8

  {
    "computer_id": "COMP-0",
    "software": [
      {
        "software_release": "http://example.com/example.cfg",
        "status": "install" # one of: install, uninstall
      },
    ],
    "partition": [
      {
        "title": "slapart1",
        "instance_id": "foo",
        "status": "start", # one of: start, stop, destroy
        "software_release": "http://example.com/example.cfg"
      },
      {
        "title": "slapart2",
        "instance_id": "bar",
        "status": "stop", # one of: start, stop, destroy
        "software_release": "http://example.com/example.cfg"
      },
    ],
  }

Modifying computer
------------------

Modify computer information in the system

`Request`::

  PUT http://example.com/api/v1/computer/{computer_id} HTTP/1.1
  Accept: application/json
  Content-Type: application/json; charset=utf-8

`Route values`:

* ``computer_id``: the ID of the computer

`Expected Request Body`::

  {
    "partition": [
      {
        "title": "part1",
        "public_ip": "::1",
        "private_ip": "127.0.0.1",
        "tap_interface": "tap2",
      },
    ],
    "software": [
      {
        "software_release": "http://example.com/example.cfg",
        "status": "installed", # one of: installed, uninstalled, error
        "log": "Installation log"
      },
    ],
  }

Where ``partition`` and ``software`` keys are optional, but at least one is required.

`Expected Response`::

  HTTP/1.1 200 OK
  Content-Type: application/json; charset=utf-8

Supplying new software
----------------------

Request to supply a new software release on a computer

`Request`::

  POST http://example.com/api/v1/computer/{computer_id}/supply HTTP/1.1
  Accept: application/json
  Content-Type: application/json; charset=utf-8

`Route values`:

* ``computer_id``: the ID of the computer

`Expected Request Body`::

  {
    "software_release": "http://example.com/example.cfg"
  }

`Expected Response`::

  HTTP/1.1 200 OK
  Content-Type: application/json; charset=utf-8

Bang computer
-------------

Request update on all partitions

`Request`::

  POST http://example.com/api/v1/computer/{computer_id}/bang HTTP/1.1
  Accept: application/json
  Content-Type: application/json; charset=utf-8

`Route values`:

* ``computer_id``: the ID of the computer

`Expected Request Body`::

  {
    "log": "Explain why this method was called",
  }

`Expected Response`::

  HTTP/1.1 200 OK
  Content-Type: application/json; charset=utf-8

Report usage
------------

Report computer usage

`Request`::

  POST http://example.com/api/v1/computer/{computer_id}/report HTTP/1.1
  Accept: application/json
  Content-Type: application/json; charset=utf-8

`Route values`:

* ``computer_id``: the ID of the computer

`Expected Request Body`::

  {
    "title": "Resource consumptions",
    "start_date": "2011/11/15",
    "stop_date": "2011/11/16",
    "movement": [
      {
        "resource": "CPU Consumption",
        "title": "line 1",
        "reference": "slappart0",
        "quantity": 42.42
      }
    ]
  }

`Expected Response`::

  HTTP/1.1 200 OK
  Content-Type: application/json; charset=utf-8
