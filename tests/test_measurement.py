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


import datetime
import dateutil.tz
from pytest import raises
import time

from unide.util import loads, dumps, local_now
from unide.common import Device
from unide.measurement import (Measurement, MeasurementPayload, Part,
                               Series, Limit, Limits)

import schemata


def test_limit():
    limit = Limit(upperError=1.0)
    assert limit.upperError == 1.0
    # Unused fields are `None`
    assert limit.lowerError is None


def test_limit_fail():
    with raises(TypeError):
        Limit(noExtremes=False)


def test_limits1():
    limits = Limits("temperature")
    limits.add_dimension("pressure")
    limits.pressure.upperWarning = 34.0
    assert not limits.problems()


def test_get():
    device = Device(deviceID="09802")
    assert device.deviceID == "09802"
    device.deviceID = "09803"
    assert device.deviceID == "09803"
    del device.deviceID
    device.deviceID = "123"
    assert device.deviceID == "123"
    assert "deviceID" in device._data
    device = Device(deviceID="098123908", supplier="Bosch", serialno="298882")
    assert device.metaData["supplier"] == "Bosch"
    assert device.metaData["serialno"] == "298882"


def test_too_long():
    with raises(ValueError):
        Device(deviceID=40 * "-")


def test_map():
    device = Device(deviceID="123")
    device.metaData["key"] = "123"
    assert device.metaData["key"] == "123"


def test_measurement(n=10):
    m = Measurement()
    m.series.add_dimension("pressure")
    m.series.add_dimension("temperature")
    for i in range(n):
        m.add_sample(local_now(),
                     temperature=36.71+i,
                     pressure=4.1+i)
        time.sleep(0.01)
    return m


def test_measurement_alternate_api():
    m = Measurement()
    m.series.add_dimension("torque")
    m.series.offsets.append(0)
    m.series.torque.append(10.2)
    m.series.offsets.append(12)
    m.series.torque.append(10.4)


def roundtrip(obj):
    clone = loads(dumps(obj))
    assert obj == clone


def test_measurement_payload():
    payload = MeasurementPayload(
        device=Device(deviceID="99232"),
        part=Part(partID="884838", result="OK", markup="scrap after use"))
    payload.measurements.append(test_measurement(3))
    m1 = payload.measurements[0]
    m1.limits.add_dimension("pressure")
    m1.limits.pressure.upperError = 4.2
    roundtrip(payload)


def test_limits():
    m = test_measurement(1)
    m.limits.add_dimension("pressure")
    m.limits.pressure.upperError = 422
    assert m.limits.pressure.upperError == 422


MEAS1 = '''{
  "content-spec": "urn:spec://eclipse.org/unide/measurement-message#v2",
  "device": {
    "deviceID": "a4927dad-58d4-4580-b460-79cefd56775b"
  },
  "part": {
    "partID": "P918298",
    "result": "OK"
  },
  "measurements": [{
    "ts": "2002-05-30T09:30:10.123+02:00",
    "series": {
      "$_time": [ 0, 23, 24 ],
      "temperature": [ 45.4231, 46.4222, 44.2432]
    }
  }, {
    "ts": "2002-05-30T09:30:10.123+02:00",
    "series": {
      "$_time": [ 0, 13, 26 ],
      "pressure": [ 52.4, 46.32, 44.2432 ]
    },
    "limits": {
      "pressure": {
        "upperError": 422
      }
    }
  }]
}'''


def test_parse_measurement():
    meas_msg = loads(MEAS1)
    assert meas_msg.device.deviceID == "a4927dad-58d4-4580-b460-79cefd56775b"
    assert meas_msg.part.partID == "P918298"
    assert len(meas_msg.measurements) == 2
    samples = list(meas_msg.measurements[0].samples())
    assert len(samples) == 3
    tz_plus2 = dateutil.tz.tzoffset("+02:00", 2 * 60 * 60)
    assert samples[0] == {
        "ts": datetime.datetime(2002, 5, 30, 9, 30, 10, 123000, tz_plus2),
        "temperature": 45.4231,
    }, samples[0]
    assert samples[1] == {
        "ts": datetime.datetime(2002, 5, 30, 9, 30, 10, 146000, tz_plus2),
        "temperature": 46.4222,
    }, samples[1]
    m2 = meas_msg.measurements[1]
    assert m2.limits.pressure.upperError == 422

    schemata.validate_measurement(meas_msg)


def test_series():
    s = Series("pressure", "temperature")
    s.add_sample(0, pressure=1.0, temperature=36.7)
    s.add_sample(10, pressure=2.0)
    s.add_sample(20, temperature=38.2)
    assert s.offsets == [0, 10, 20]
    assert s.temperature == [36.7, None, 38.2]
    assert s.pressure == [1.0, 2.0, None]
    s.add_dimension("torque")
    s.torque = [1, 2, 4]


def test_convenience_api():
    d = Device("12345", maker="Bosch")
    msg = loads(d.measurement(temperature=36.7))
    assert msg.device.deviceID == d.deviceID
    assert msg.device.metaData["maker"] == "Bosch"
    assert msg.measurements[0].series.temperature == [36.7]
