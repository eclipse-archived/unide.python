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

"""Support code for PPMP."""

import datetime
import json

import dateutil.parser
import dateutil.tz

CONTENT_SPECS = {}


def payload_wrapper(cls):
    """This is a class wrapper that registers a PPMP payload with the
    content-spec registry.
    """
    CONTENT_SPECS[cls.CONTENT_SPEC] = cls
    return cls


def local_now():
    """The current timestamp in the local timezone."""
    return datetime.datetime.now(dateutil.tz.tzlocal())


def local_timezone(value):
    """Add the local timezone to `value` to make it aware."""
    if hasattr(value, "tzinfo") and value.tzinfo is None:
        return value.replace(tzinfo=dateutil.tz.tzlocal())
    return value


class ValidationError(Exception):
    """An exception for PPMP validation errors."""

    def __init__(self, errors):
        Exception.__init__(self, "\n".join(errors))


def loads(data, validate=False, **kwargs):
    """Load a PPMP message from the JSON-formatted string in `data`. When
    `validate` is set, raise `ValidationError`. Additional keyword
    arguments are the same that are accepted by `json.loads`,
    e.g. `indent` to get a pretty output.
    """
    d = json.loads(data, **kwargs)
    content_spec = d["content-spec"]
    Payload = CONTENT_SPECS[content_spec]
    payload = Payload.load(d)
    if validate:
        errors = payload.problems()
        if errors:
            raise ValidationError(errors)
    return payload


def dumps(data, **kwargs):
    """Convert a PPMP entity to JSON. Additional arguments are the same as
    accepted by `json.dumps`."""

    def _encoder(value):
        if isinstance(value, datetime.datetime):
            return value.isoformat()

        if hasattr(value, "_data"):
            return value._data

        raise TypeError('Could not encode %r' % value)

    return json.dumps(data, default=_encoder, **kwargs)
