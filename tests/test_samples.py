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


def test_measurement():
    data = open("tests/measurement.json").read()
    msg = dumps(loads(data))
    orig = json.loads(data)
    out = json.loads(msg)
    assert orig == out


def test_message():
    data = open("tests/message.json").read()
    msg = dumps(loads(data))
    orig = json.loads(data)
    out = json.loads(msg)
    assert orig == out


def test_process():
    data = open("tests/process.json").read()
    msg = dumps(loads(data))
    orig = json.loads(data)
    out = json.loads(msg)
    assert orig == out


def test_validation1():
    with raises(ValidationError):
        data = open("tests/invalid.json").read()
        loads(data, validate=True)


def test_validation2():
    data = open("tests/invalid.json").read()
    msg = loads(data, validate=False)
    errors = msg.problems()
    assert len(errors) > 0
    msg = dumps(loads(data))
    orig = json.loads(data)
    out = json.loads(msg)
    assert orig == out
