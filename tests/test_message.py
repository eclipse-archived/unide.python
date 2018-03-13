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

# flake8: noqa
import datetime
import dateutil.tz
from pytest import raises

from unide.util import loads, dumps
from unide.common import Device
from unide.message import Message, MessagePayload

import schemata


def roundtrip(obj):
    clone = loads(dumps(obj))
    assert obj == clone


def test_create_message():
    msg = MessagePayload(device=Device(deviceID="29038409"))
    assert msg.device.deviceID == "29038409"
    assert len(msg.messages) == 0
    msg.messages.append(Message(code="190AB", nonsense="no sense"))
    assert len(msg.messages) == 1
    assert msg.messages[0].code == "190AB"
    roundtrip(msg)


def test_check_mandatory():
    with raises(ValueError):
        Message(code=None)


MINIMAL = '''{
  "content-spec":"urn:spec://eclipse.org/unide/machine-message#v2",
  "device": {
    "deviceID": "2ca5158b-8350-4592-bff9-755194497d4e"
  },
  "messages": [{
    "ts": "2002-05-30T09:30:10.123+02:00",       
    "code": "190ABT"
  }]
}'''


def test_load_minimal():
    msg = loads(MINIMAL)
    assert msg.device.deviceID == "2ca5158b-8350-4592-bff9-755194497d4e"
    assert len(msg.messages) == 1

    tz_plus2 = dateutil.tz.tzoffset("+02:00", 2 * 60 * 60)

    m = Message(ts=datetime.datetime(2002, 5, 30, 9, 30, 10, 123000, tz_plus2),
                code="190ABT")
    assert msg.messages[0] == m
    schemata.validate_message(msg)


def test_make_minimal():
    Device("2ca5158b-8350-4592-bff9-755194497d4e")


MULTIPLE = '''{
  "content-spec":"urn:spec://eclipse.org/unide/machine-message#v2",
  "device": {
    "deviceID": "2ca5158b-8350-4592-bff9-755194497d4e",
    "operationalStatus": "normal",
    "metaData":{
      "swVersion": "2.0.3.13",
      "swBuildID": "41535"
    }
  },
  "messages": [{
    "origin": "sensor-id-992.2393.22",
    "ts": "2002-05-30T09:30:10.123+02:00",
    "type": "DEVICE",
    "severity": "HIGH",
    "code": "190ABT",
    "title": "control board damaged",
    "description": "Electronic control board or its electrical connections are damaged", 
    "hint": "Check the control board",
    "metaData": {
      "firmware": "20130304_22.020"
    }
  }, {
    "ts": "2002-05-30T09:30:10.125+02:00",
    "type": "TECHNICAL_INFO",
    "severity": "HIGH",
    "code": "33-02",
    "title": "Disk size limit reached",
    "description": "Disk size has reached limit. Unable to write log files."
  }]
}'''


def test_load_multiple():
    msg = loads(MULTIPLE)
    assert msg.device.deviceID == "2ca5158b-8350-4592-bff9-755194497d4e"
    assert msg.device.metaData["swVersion"] == "2.0.3.13"
    
    assert len(msg.messages) == 2
    
    assert msg.messages[0].origin == "sensor-id-992.2393.22"
    assert msg.messages[0].type == "DEVICE"
    assert msg.messages[0].severity == "HIGH"
    assert msg.messages[0].hint == "Check the control board"
    assert msg.messages[0].metaData["firmware"] == "20130304_22.020"

    schemata.validate_message(msg)


def test_convience_api():
    device = Device(deviceID="2098390", supplier="Contact")
    msg = loads(device.message("AB910T", hint="Axis is broken"))
    assert msg.device.deviceID == "2098390"
    assert msg.messages[0].code == "AB910T"

    schemata.validate_message(msg)
