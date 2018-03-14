#!/usr/bin/env python
# coding: utf-8
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

import os
import json
from jsonschema import validate
from functools import partial

from unide.util import dumps

__all__ = ['validate_measurement', 'validate_message', 'validate_process']


here = os.path.dirname(__file__)


def read_json(f):
    with open(os.path.join(here, f)) as f:
        return json.load(f)


def validate_object(ppmp_obj, schema):
    validate(json.loads(dumps(ppmp_obj)), schema)


validate_measurement = partial(validate_object,
                               schema=read_json('measurement_schema.json'))
validate_message = partial(validate_object,
                           schema=read_json('message_schema.json'))
validate_process = partial(validate_object,
                           schema=read_json('process_schema.json'))
