# Copyright (c) 2017 Contact Software.
#
# All rights reserved. This program and the accompanying materials are
# made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution.
#
# The Eclipse Public License is available at
#     http://www.eclipse.org/legal/epl-v10.html

from unide.util import loads, dumps, ValidationError
import json

from pytest import raises

import schemata


def read(path):
    with open(path) as f:
        return f.read()


def test_measurement():
    data = read("tests/measurement.json")
    msg = dumps(loads(data))

    orig = json.loads(data)
    out = json.loads(msg)
    assert orig == out

    print json.dumps(out, indent=2)
    schemata.validate_measurement(loads(data))


def test_message():
    data = read("tests/message.json")
    msg = dumps(loads(data))
    orig = json.loads(data)
    out = json.loads(msg)
    assert orig == out

    schemata.validate_message(loads(data))


def test_process():
    data = read("tests/process.json")
    msg = dumps(loads(data))
    orig = json.loads(data)
    out = json.loads(msg)
    assert orig == out

    schemata.validate_process(loads(data))


def test_validation1():
    with raises(ValidationError):
        data = read("tests/invalid.json")
        loads(data, validate=True)


def test_validation2():
    data = read("tests/invalid.json")
    msg = loads(data, validate=False)
    errors = msg.problems()
    assert len(errors) > 0
    msg = dumps(loads(data))
    orig = json.loads(data)
    out = json.loads(msg)
    assert orig == out
