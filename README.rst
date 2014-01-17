.. image:: https://travis-ci.org/badele/serialkiller.png?branch=master
   :target: https://travis-ci.org/badele/serialkiller

.. image:: https://coveralls.io/repos/badele/serialkiller/badge.png
   :target: https://coveralls.io/r/badele/serialkiller

.. disableimage:: https://pypip.in/v/serialkiller/badge.png
   :target: https://crate.io/packages/serialkiller/

.. disableimage:: https://pypip.in/d/serialkiller/badge.png
   :target: https://crate.io/packages/serialkiller/



About
=====

``serialkiller`` time series database with reduce system, it kill the same time series ! :)

``serialkiller`` can be used in three different ways:
- In command line
- In http API REST mode
- With library

Installing
==========

To install the latest release from `PyPI <http://pypi.python.org/pypi/serialkiller>`_

.. code-block:: console

    $ pip install serialkiller

To install the latest development version from `GitHub <https://github.com/badele/serialkiller>`_

.. code-block:: console

    $ pip install git+git://github.com/badele/serialkiller.git

Configuration
=============

Copy sk_server.cfg from serialkiller package to /etc/sk_server.cfg and edit your ``.bashrc``, add this line 

.. code-block:: console

   SERIALKILLER_SETTINGS=/etc/sk_server.cfg

The default `sk_server.cfg`

.. code-block:: console

   STORAGE = "/tmp/sensors"
   HOST = 0.0.0.0
   PORT = 80
   DEBUG = False

Now you can run the serialkiller standalone server with `sk_standalone`

.. code-block:: console

   sk_standalone &

You can now use the `serialkiller-plugins <https://github.com/badele/serialkiller-plugins>`_ for push the sensors results 

You can also point your web navigator to http://youipserver, that return the list of all functions in JSON format, sample result: 

.. code-block:: console

   {

         "/": "All serialkiller API functions",
         "/api/1.0/": "All serialkiller API functions",
         "/api/1.0/addEvent/<sensorid>/<type>/<values>": "Add a new event, no deduplicate",
         "/api/1.0/addValue/<sensorid>/<type>/<values>": "Add a new value, deduplicate line",
         "/api/1.0/list": "List all last sensors"
   }

