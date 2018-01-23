============
Unide Python
============

.. image:: https://img.shields.io/travis/eclipse/unide.python/master.svg
    :alt: Travis-CI badge
    :target: https://travis-ci.org/eclipse/unide.python

.. image:: https://img.shields.io/coveralls/eclipse/unide.python/master.svg
    :alt: Coveralls badge
    :target: https://coveralls.io/r/eclipse/unide.python?branch=master

.. .. image:: https://img.shields.io/pypi/v/unide-python.svg
    :alt: PyPI latest version badge
    :target: https://pypi.python.org/pypi/unide-python/

.. image:: https://readthedocs.org/projects/unidepython/badge/?version=latest
   :alt: Read the Docs
   :target: http://unidepython.readthedocs.io/en/latest/

.. .. image:: https://img.shields.io/pypi/format/unide-python.svg
    :alt: Download format
    :target: http://pythonwheels.com/

.. .. image:: https://img.shields.io/pypi/l/unide-python.svg
    :alt: Unide license
    :target: https://pypi.python.org/pypi/unide-python/

This Python package is part of the `Eclipse Unide Project
<https://www.eclipse.org/unide>`_ and provides an API for generating,
parsing and validating PPMP payloads. PPMP, the `"Production
Performance Management Protocol"
<https://www.eclipse.org/unide/specification>`_ is a simple,
JSON-based protocol for message payloads in (Industrial) Internet of
Things applications defined by the `Eclipse IoT Working Group
<https://iot.eclipse.org/>`_. Implementations for other programming
languages are available from the Unide web site.

The focus of the Python implementation is ease of use for backend
implementations, tools and for prototyping PPMP
applications. Generating a simple payload and sending it over MQTT
using `Eclipse Paho <https://github.com/eclipse/paho.mqtt.python>`_ is
a matter of just a few lines::

  >>> import unide
  >>> import paho.mqtt.client as mqtt
  >>> client = mqtt.Client()
  >>> client.connect("localhost", 1883, 60)
  >>> device = unide.Device("Device-001")
  >>> measurement = device.measurement(temperature=36.7)
  >>> client.publish(topic="sample", measurement)

Installation
============

The latest version is available in the Python Package Index (PyPI) and
can be installed using::

  pip install unide-python

``unide-python`` can be used with Python 2.7, 3.4, 3.5 and 3.6.

Source code, including examples and tests, is available on GitHub:
https://github.com/eclipse/unide.python

To install the package from source::

  git clone git@github.com:eclipse/unide.python.git
  cd unide.python
  python setup.py install


Contributing
============

This is a straightforward Python project, using `setuptools` and the
standard ``setup.py`` mechanism. You can run the test suite using
``setup.py``::

  python setup.py test

There also is a top-level ``Makefile`` that builds a development
environment and can run a couple of developer tasks. We aim for 100%
test coverage and use `tox <https://pypi.python.org/pypi/tox>`_ to
test against all supported Python releases. To run all tests against
all supported Python versions, build the documentation locally and an
installable wheel, you'll require `pyenv
<https://github.com/pyenv/pyenv>`_ and a decent implementation of
make. ``make all`` will create a virtualenv ``env`` in the project
directory and install the necessary tools (see ``tools.txt``).

For bug reports, suggestions and questions, simply open an issue in
the Github issue tracker. We welcome pull requests.


Documentation
=============

Detailed documentation is available on Read the Docs:
http://unidepython.readthedocs.io/en/latest/.
