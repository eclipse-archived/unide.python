#!/usr/bin/env python
# -*- Python -*-
#
# Copyright (c) 2017 Contact Software.
#
# All rights reserved. This program and the accompanying materials are
# made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution.
#
# The Eclipse Public License is available at
#     http://www.eclipse.org/legal/epl-v10.html

"""This Python package is part of the Eclipse Unide Project and
provides an API for generating, parsing and validating PPMP
payloads. PPMP, the "Production Performance Management Protocol" is a
simple, JSON-based protocol for message payloads in (Industrial)
Internet of Things applications defined by the Eclipse IoT Working
Group. Implementations for other programming languages are available
from the Unide web site.
"""

# flake8: noqa
from . import common
from . import measurement
from . import message
from . import process
from . import schema
