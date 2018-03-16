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
import numbers
import six

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


def identity(x):
    """
    Identity function

    """
    return x


class Property(object):
    """A PPMP property, described by name, type, max. length etc."""

    # pylint: disable=too-many-instance-attributes
    def __init__(self,
                 name=None,
                 types=None,
                 oneof=None,
                 length=None,
                 default=lambda: None,
                 null=True,
                 convert=identity,
                 load=identity):
        # pylint: disable=too-many-arguments
        self._name = name
        self._default = default
        self._null = null
        self._types = types
        self._length = length
        self._oneof = oneof
        self._convert = convert
        self._load = load

    def _has_wrong_type(self, fieldname, value, errors):
        if self._types and not isinstance(value, self._types):
            errors.append("%r is not an appropriate value "
                          "for %s (wrong type)" % (value, fieldname))
            return True

        return False

    def _has_wrong_length(self, fieldname, value, errors):
        if self._length is not None and len(value) > self._length:
            errors.append("%s may not be longer than %s" % (fieldname, self._length))
            return True

        return False

    def _is_not_one_of(self, fieldname, value, errors):
        if self._oneof is not None and value not in self._oneof:
            errors.append("%r must be one of %s for %s" %
                          (value, ", ".join(str(x) for x in self._oneof), fieldname))
            return True

        return False

    @staticmethod
    def _has_subproblems(fieldname, value, errors):
        # pylint: disable=unused-argument
        if hasattr(value, "problems"):
            value.problems(errors)
            return True

        return False

    def check(self, obj, value, errors):
        """
        Check if `value` is valid this property in the entity `obj`. Append
        validation results to `errors` (list).

        """
        fieldname = "%s.%s" % (type(obj).__name__, self._name)

        if value is None:
            if not self._null:
                errors.append("%s may not be 'null'" % fieldname)

            # If None, just leave. The rest of checks don't make any sense.
            return

        for has_error in [self._has_wrong_type, self._has_wrong_length,
                          self._is_not_one_of, self._has_subproblems]:
            if has_error(fieldname, value, errors):
                break

    def load(self, value):
        """Load a property value from its JSON representation."""
        return self._load(value)

    def convert(self, value):
        """Convert a value from Python to an internal representation that is
        conformant.
        """
        return self._convert(value)

    def __get__(self, obj, cls=None):
        return obj._data.setdefault(self._name, self._default())

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


class MetaObject(type):
    """
    Metaclass for `Object` classes

    """

    def __init__(cls, name, bases, kwattrs):
        # Synchronize the class attribute name with the Property._name
        for key, value in kwattrs.items():
            if isinstance(value, Property) and value._name is None:
                value._name = key

        super(MetaObject, cls).__init__(name, bases, kwattrs)


@six.add_metaclass(MetaObject)
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

        for name, value in kwargs.items():
            setattr(self, name, value)

        return self

    def is_excess_field_ok(self, name):
        """True, if this entity is allowed to have freely named keys."""
        # pylint: disable=unused-argument, no-self-use
        return False

    def problems(self, errors=None):
        """Apply validation checks to this entity, and return a list of
        problems. If `errors` is not None it must be a list to which
        all validation problems will be added.
        """
        if errors is None:
            errors = []

        cls = type(self)
        existing_fields = set(self._data)

        content_spec = getattr(cls, "CONTENT_SPEC", None)
        if content_spec:
            if self._data.get("content-spec") != content_spec:
                errors.append(
                    "'content-spec' for '%s' wrong or missing" % cls.__name__)
            existing_fields.remove("content-spec")

        for name, prop in self.get_properties().items():
            if name in existing_fields:
                existing_fields.remove(name)
                value = self._data.get(name)
                prop.check(self, value, errors)

        for excess_field in existing_fields:
            if not self.is_excess_field_ok(excess_field):
                errors.append("'%s' is not a valid key for '%s' objects" %
                              (excess_field, cls.__name__))

        return errors

    @classmethod
    def load(cls, data):
        """Create an object of type `cls` using the `data`, that has been
        created by reading a JSON.

        :type data: dict
        :rtype: cls

        """
        self = make_object(cls, data)

        props = cls.get_properties()

        for key, value in data.items():
            prop = props.get(key)

            if prop is not None:
                setattr(self, key, prop.load(value))

        return self

    def __eq__(self, other):
        return self._data == other._data

    def __ne__(self, other):
        return not self == other

    def __str__(self):
        return "%s(%s)" % (
            type(self).__name__,
            ", ".join(["%s=%s" % pair for pair in self._data.items()]))

    __repr__ = __str__

    @classmethod
    def get_properties(cls):
        """
        Returns a dict {prop-name: prop object} of class attributes that are
        `Property` instances.

        The property name is read from the property object. This is normally
        the same as the class attribute, but does not necessarily have to.

        """
        return {
            attr._name: attr for attr in vars(cls).values()
            if isinstance(attr, Property)
        }


def make_object(cls, data):
    """Creates an API object of class `cls`, setting its `_data` to
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

        for key, value in data.items():
            self.add_dimension(key, value)

        return self


def to_string(value):
    """Convert value to string."""
    if isinstance(value, stringy_types):
        value = str(value)

    return value


def String(length=None, **kwargs):
    """A string valued property with max. `length`."""
    return Property(
        length=length,
        types=stringy_types,
        convert=to_string,
        **kwargs
    )


def Float(**kwargs):
    """A float property."""
    return Property(types=float, convert=float, **kwargs)


def Integer(**kwargs):
    """An integer property."""
    return Property(types=int, convert=int, **kwargs)


def Map(**kwargs):
    """A property that is a String:String map."""
    return Property(default=StringMap, **kwargs)


def NumberMap(**kwargs):
    """A Property that is a String:Float map"""
    return Property(default=Float, **kwargs)


def Datetime(null=True, **kwargs):
    """A datetime property."""
    return Property(
        types=datetime.datetime,
        convert=util.local_timezone,
        load=dateutil.parser.parse,
        null=null,
        **kwargs
    )


def InstanceOf(cls, **kwargs):
    """A property that is an instance of `cls`."""
    return Property(types=cls, load=cls.load, **kwargs)


def ListOf(cls, **kwargs):
    """A property that is a list of `cls`."""

    def _list_load(value):
        return [cls.load(d) for d in value]

    return Property(types=list, load=_list_load, default=list, **kwargs)


class StringMap(OrderedDict):
    """A dictionary mapping strings to strings."""

    def __setitem__(self, key, value, dict_setitem=dict.__setitem__):
        if isinstance(key, stringy_types) and isinstance(value, stringy_types):
            super(StringMap, self).__setitem__(key, value)
        else:
            raise ValueError("StringMap requires strings for keys and values")


class RealNumberMap(OrderedDict):
    """Dictionary string to real number"""

    def __setitem__(self, key, value, dict_setitem=dict.__setitem__):
        if not isinstance(key, stringy_types):
            raise ValueError('NumberMap requires strings for keys')

        if not isinstance(value, numbers.Real):
            raise ValueError('NumberMap requires real numbers for keys')

        super(RealNumberMap, self).__setitem__(key, value)
