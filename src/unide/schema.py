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

"""Base classes for PPMP entities and properties."""

import datetime
from collections import OrderedDict
import dateutil.parser

from . import util

# Standardize to py3's str and bytes
try:
    str = unicode  # pylint: disable=redefined-builtin
except NameError:
    pass

stringy_types = str, bytes


__all__ = [
    "Object",
    "make_object",
    "Property",
    "String",
    "Float",
    "Datetime",
    "Map",
    "InstanceOf",
]


class Object(object):
    """All JSON-serializable things are represented as specializations of
    `Object` that provide an API to work with that particular part of
    the PPMP payload. All PPMP properties are stored in a separate
    dict called `_data`. This allows us to simply feed `_data` into
    the JSON serializer. When ingesting a PPMP message, `Object.load`
    *replaces* `_data` with the dict from `json.load`, and
    specializations of `load` replace sub-structures with API wrappers
    by building an empty wrapper and settings it `_dict` to the
    sub-structure.
    """

    def __new__(cls, *args, **kwargs):
        # `Object` does not have `__init__` but `__new__` to setup a
        # new API object. This removes the need for specializations to
        # call super's `__init__` and makes creating convenience
        # constructors for API classes straightforward.

        # pylint: disable=unused-argument
        self = object.__new__(cls)
        self._data = OrderedDict()
        for name, value in list(kwargs.items()):
            setattr(self, name, value)
        return self

    def is_excess_field_ok(self, name):
        """True, if this entities is allowed to have freely named keys."""
        # pylint: disable=unused-argument, no-self-use
        return False

    def problems(self, errors=None):
        """Apply validation checks to this entity, and return a list of
        problems. If `errors` is not None it must be a list to which
        all validation problems will be added.
        """
        if errors is None:
            errors = list()
        cls = type(self)
        existing_fields = set(self._data.keys())
        props = [(p._name, p) for p in cls.__dict__.values()
                 if isinstance(p, Property)]

        content_spec = getattr(cls, "CONTENT_SPEC", None)
        if content_spec:
            if self._data.get("content-spec", None) != content_spec:
                errors.append(
                    "'content-spec' for '%s' wrong or missing" % cls.__name__)
            existing_fields.remove("content-spec")

        while props:
            name, prop = props.pop()
            if name in existing_fields:
                existing_fields.remove(name)
                value = getattr(self, name, None)
                prop.check(self, value, errors)
        for excess_field in existing_fields:
            if not self.is_excess_field_ok(excess_field):
                errors.append("'%s' is not a valid key for '%s' objects" %
                              (excess_field, cls.__name__))
        return errors

    @classmethod
    def load(cls, data):
        """Create an object of type `cls` using the dict `data`, that has been
        created by a JSON readed.
        """
        self = make_object(cls, data)
        props = dict((p._name, p) for k, p in list(cls.__dict__.items())
                     if isinstance(p, Property))
        for key, value in list(data.items()):
            prop = props.get(key)
            if prop is not None:
                setattr(self, key, prop.load(value))
        return self

    def __eq__(self, other):
        return self._data.__eq__(other._data)

    def __ne__(self, other):
        return not self == other

    def __str__(self):
        return "%s(%s)" % (
            type(self).__name__,
            ", ".join(["%s=%s" % (k, v) for k, v in list(self._data.items())]))

    __repr__ = __str__


def make_object(cls, data):
    """Creates on API object of class `cls`, setting its `_data` to
    data. Subclasses of `Object` are required to use this to build a
    new, empty instance without using their constructor.
    """
    if issubclass(cls, Object):
        self = object.__new__(cls)
        self._data = data
    else:
        self = data
    return self


class HasDimensions(Object):
    """A PPMP entity that can have extra properties, as in PPMP series
    data.
    """

    def __init__(self, *dimensions):
        self.dimensions = set()
        for dim in dimensions:
            self.add_dimension(dim)

    def is_excess_field_ok(self, name):
        """True, if the property named `name` is one of the dimensions."""
        return name in self.dimensions

    def add_dimension(self, name, data=None):
        """Add a named dimension to this entity."""
        self.dimensions.add(name)
        if data is None:
            valobj = self.__dimtype__()
        else:
            valobj = make_object(self.__dimtype__, data)
        self._data[name] = valobj
        setattr(self, name, valobj)
        return valobj

    def __dimtype__(self):
        # To be overriden by subclasses
        raise NotImplementedError

    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, value):
        if key not in self.dimensions:
            self.add_dimension(key)
        return setattr(self, key, value)

    @classmethod
    def load(cls, data):
        self = make_object(cls, data)
        self.dimensions = set()
        for key, value in list(data.items()):
            self.add_dimension(key, value)
        return self


class Property(object):
    """A PPMP property, described by name, type, max. length etc."""

    # pylint: disable=too-many-instance-attributes
    def __init__(self,
                 name,
                 types=None,
                 oneof=None,
                 length=None,
                 default=None,
                 null=True,
                 convert=None,
                 load=None):
        # pylint: disable=too-many-arguments
        self._name = name
        self._default = default
        self._null = null
        self._types = types
        self._length = length
        self._oneof = oneof
        self._convert = convert
        self._load = load

    # pylint: disable=unused-argument
    def _check_null(self, fieldname, obj, value, errors):
        if value is None:
            if not self._null:
                errors.append("%s may not be 'null'" % fieldname)
            return True

        return False

    def _check_type(self, fieldname, obj, value, errors):
        if self._types and not isinstance(value, self._types):
            errors.append("%r is not an appropriate value "
                          "for %s (wrong type)" % (value, fieldname))
            return True

        return False

    def _check_length(self, fieldname, obj, value, errors):
        if self._length is not None:
            if len(value) > self._length:
                errors.append("%s may not be longer than %s" % (fieldname,
                                                                self._length))
            return True

        return False

    def _check_one_of(self, fieldname, obj, value, errors):
        if self._oneof:
            if value not in self._oneof:
                errors.append("%r must be one of %s" %
                              (value, ", ".join(str(x) for x in self._oneof)))
            return True

        return False

    def _check_problems(self, fieldname, obj, value, errors):
        # pylint: disable=no-self-use
        if hasattr(value, "problems"):
            value.problems(errors)
            return True

        return False

    def check(self, obj, value, errors):
        """Check if `value` is valid this property in the entity `obj`. Append
        validation results to `errors` (list).
        """
        fieldname = "%s.%s" % (type(obj).__name__, self._name)
        for checker in (self._check_null, self._check_type, self._check_length,
                        self._check_one_of, self._check_problems):
            if checker(fieldname, obj, value, errors):
                break
        return len(errors) == 0

    def load(self, value):
        """Load a property value from its JSON representation."""
        if self._load:
            value = self._load(value)
        return value

    def convert(self, value):
        """Convert a value from Python to an internal representation that is
        conformant.
        """
        if self._convert is not None:
            value = self._convert(value)
        return value

    def __get__(self, obj, cls=None):
        if self._default:
            return obj._data.setdefault(self._name, self._default())
        return obj._data.get(self._name, None)

    def __set__(self, obj, value):
        errors = []
        if value is None:
            # We don't want non-existing properties to appear as
            # 'null' in the JSON output, thus we'll remove the key
            # here, but we'll still have to check for null.
            self.check(obj, value, errors)
            self.__delete__(obj)
        else:
            value = self.convert(value)
            self.check(obj, value, errors)
            if not errors:
                obj._data[self._name] = value
        if errors:
            raise ValueError("\n".join(errors))

    def __delete__(self, obj):
        # NOTE [bgu 22-09-2017]: .pop with default allows
        # not to check if key is present
        obj._data.pop(self._name, None)


def to_string(value):
    """Convert value to string."""
    if isinstance(value, stringy_types):
        value = str(value)
    return value


def String(name, length=None, **kwargs):
    """A string valued property with max. `length`."""
    return Property(
        name, length=length, types=stringy_types, convert=to_string, **kwargs)


def Float(name, **kwargs):
    """A float property."""
    return Property(name, types=float, convert=float, **kwargs)


def Map(name, *args, **kwargs):
    """A property that is a String:String map."""
    return Property(name, default=StringMap, *args, **kwargs)


def Datetime(name, null=True):
    """A datetime property."""
    return Property(
        name,
        types=datetime.datetime,
        convert=util.local_timezone,
        load=dateutil.parser.parse,
        null=null)


def InstanceOf(name, cls, **kwargs):
    """A property that is an instance of `cls`."""
    return Property(name, types=cls, load=cls.load, **kwargs)


def ListOf(name, cls):
    """A property that is a list of `cls`."""

    def _list_load(value):
        return [cls.load(d) for d in value]

    return Property(name, types=list, load=_list_load, default=list)


class StringMap(OrderedDict):
    """A dictionary mapping strings to strings."""

    def __setitem__(self, key, value, dict_setitem=dict.__setitem__):
        if isinstance(key, stringy_types) and isinstance(value, stringy_types):
            super(StringMap, self).__setitem__(key, value)
        else:
            raise ValueError("StringMap requires strings for keys and values")
