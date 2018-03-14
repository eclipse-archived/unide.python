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

import datetime
import dateutil.tz
from unide.schema import Object, String, Float, Property, Datetime, StringMap
from pytest import raises


def test_empty_object():
    a = Object()
    assert str(a) == "Object()"
    b = Object()
    assert a is not b
    assert a == b


class BasicFields(Object):
    f_string = String(20, null=False)
    f_float = Float()
    f_datetime = Datetime()
    f_enum = String(oneof=["A", "B", "C"])


def test_basic_fields():
    obj = BasicFields(f_string="abc",
                      f_float=1.23,
                      f_result="OK",
                      f_datetime=datetime.datetime(2001, 1, 2, 3, 4, 5, 6))
    assert obj.f_string == "abc"
    assert obj.f_float == 1.23
    assert obj.f_result == "OK"
    assert obj.f_datetime == datetime.datetime(2001, 1, 2, 3, 4, 5, 6,
                                               dateutil.tz.tzlocal())
    obj.f_string = "def"
    obj.f_float = 4.56
    obj.f_result = "NOK"
    obj.f_datetime = datetime.datetime(2001, 2, 3, 4, 5, 6, 7)
    assert obj.f_string == "def"
    assert obj.f_float == 4.56
    assert obj.f_result == "NOK"
    assert obj.f_datetime == datetime.datetime(2001, 2, 3, 4, 5, 6, 7,
                                               dateutil.tz.tzlocal())


def test_not_null():
    with raises(ValueError):
        BasicFields(f_string=None)


def test_too_long():
    with raises(ValueError):
        BasicFields(f_string=40 * "-")


def test_wrong_type():
    with raises(ValueError):
        BasicFields(f_string=0)


def test_not_one_of():
    with raises(ValueError):
        BasicFields(f_enum="X")


def test_load():
    obj = BasicFields.load({
        "f_string": "xyz",
        "f_float": 0.123,
        "f_datetime": "2002-05-30T09:30:10.123",
        })
    assert obj.f_string == "xyz"
    assert obj.f_float == 0.123
    assert obj.f_datetime == datetime.datetime(2002, 5, 30, 9, 30, 10, 123000,
                                               dateutil.tz.tzlocal())


def test_float_ok():
    # We are liberal in what we accept for a float as long as it is
    # convertible to float
    obj = BasicFields()
    obj.f_float = "1.23"
    obj.f_float = 12


def test_tz():
    obj = BasicFields()
    obj.f_datetime = datetime.datetime.now()
    assert obj.f_datetime.tzinfo == dateutil.tz.tzlocal()


def test_float_fail():
    with raises(ValueError):
        obj = BasicFields()
        obj.f_float = "foo"


def test_string_ok():
    obj = BasicFields()
    obj.f_string = "1"


def test_bad_date():
    with raises(ValueError):
        BasicFields(f_datetime="xx")


def test_default_value():

    class DefaultValue(Object):
        f_prop = Property(default=lambda: "bar")

    obj = DefaultValue()
    assert obj.f_prop == "bar"


def test_string_map():
    sm = StringMap()
    sm["key"] = "value"


def test_string_map_fail1():
    with raises(ValueError):
        sm = StringMap()
        sm["x"] = 1


def test_string_map_fail2():
    with raises(ValueError):
        sm = StringMap()
        sm[2] = "y"


def test_validation():
    obj = BasicFields(f_string="abc")
    assert not obj.problems()

    obj._data["unknown"] = "x"
    errors = obj.problems()
    assert len(errors) == 1

    obj._data["f_string"] = 1
    errors = obj.problems()
    assert len(errors) == 2

    obj._data["f_string"] = None
    errors = obj.problems()
    assert len(errors) == 2

    obj._data["f_enum"] = "X"
    errors = obj.problems()
    assert len(errors) == 3
