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

"""The measurement message is the format to exchange simple
(non-structured, non-complex ) measurement data. It also allows to
transport multiple measurement data (eg. values over time), called
'series'."""

import datetime

from .util import payload_wrapper, local_now, dumps
from .schema import (Object, make_object, Property, String, Float, Map,
                     Datetime, InstanceOf, ListOf, HasDimensions)
from .common import (Result, Code, Device)


class Limit(Object):
    """An API wrapper for the PPMP `Limit` object. All properties are
    optional.

    :param float upperError: Indicates the upper error threshold,
        given by the device/integrator. Optional.
    :param float lowerError: Indicates the lower error threshold,
        given by the device/integrator. Optional.
    :param float upperWarn: Indicates the upper warning threshold,
        given by the device/integrator. Optional
    :param float lowerWarn: Indicates the lower warning threshold,
        given by the device/integrator. Optional
    """
    upperError = Float("upperError")
    lowerError = Float("lowerError")
    upperWarning = Float("upperWarning")
    lowerWarning = Float("lowerWarning")

    def __init__(self,
                 upperError=None,
                 lowerError=None,
                 upperWarning=None,
                 lowerWarning=None):
        self.upperError = upperError
        self.lowerError = lowerError
        self.upperWarning = upperWarning
        self.lowerWarning = lowerWarning


class Limits(HasDimensions):
    """`Limits` wraps the "limits" key in a PPMP payload. The `limits`
    property in a `MeasurementPayload` objects is an instance of
    `Limits`. For the API dimensions have to be declared to the
    constructor or added one-by-one by calling
    `add_dimension()`. Declared dimensions are subsequently available
    as named attributes of the `Limits` object.

    >>> from unide.measurement import Limits
    >>> limits = Limits("temperature")
    >>> limits.temperature.upperError = 59.0
    >>> limits.temperature.lowerError = 0.0
    >>> limits.temperature.upperWarning = 45.0
    >>> limits.temperature.lowerWarning = 12.0

    **limits**

    :Definition:

       Provides information about limits for data provided in the
       series element. The limits is an JSON object where the key is
       the name of a Measurement Point (see also series element) and
       the value is a structure of different upper/lower limits.

    :Required: no

    :Size restriction: no

    :Note:

        each subfield key corresponds to one measurement point and
        holds an object with the error/warning levels.

    :Sub Fields:

        - upperError
        - lowerError
        - upperWarn
        - lowerWarn

    Example::

       ...
         "limits": {
           "temperature": {
             "upperError": 59.0,
             "lowerError": 0.0,
             "upperWarn": 45.0,
             "lowerWarn": 12.0
           }
         }
       ...

    """
    __dimtype__ = Limit


class Series(HasDimensions):
    """Wraps the "series" key in a PPMP payload.

    :Definition: The series data collected for the measurements. Every
        subfield key matches a measurement point of the device
        type. Every subfield value is an array. All arrays are of
        equal length and an entry at a given index corresponds to
        another arrays value at this index

    :Required: yes

    :Size restriction: no

    :Note: In the case of a time series, one column contains the time
       offset (positive values in ascending order starting with 0). In
       this case the key is $_time`.

    :Sub Fields:
       $_time

    Example::

        ...
        "ts": "2015-07-23T16:04:10.223+02:00",
        "series": {
           "$_time": [0, 22, 24, 27],
           "temperature": [33, 34, 33, 32]
        }
        ...
    """
    __dimtype__ = list
    offsets = Property("$_time")

    def __init__(self, *dimensions):
        super(Series, self).__init__(*dimensions)
        self.offsets = list()

    def add_sample(self, offset, **data):
        """Add a sample to this series."""
        self.offsets.append(offset)
        assert all(k in self.dimensions for k in list(data.keys()))
        for dim in self.dimensions:
            getattr(self, dim).append(data.get(dim, None))

    @classmethod
    def load(cls, data):
        self = make_object(Series, data)
        self.dimensions = set()
        for key, value in list(data.items()):
            if key != "$_time":
                self.add_dimension(key, value)
        return self


class Measurement(Object):
    """A list of sensor readings

    :Required:	yes

    :Size restriction:	no

    :Note: if sensor readings have the same timestamp/-offsets, they
        can be combined in one measurement block. Otherwise they are
        added to the measurements list as individual block.

    """
    ts = Datetime("ts", null=False)
    result = Result()
    code = Code()
    series = InstanceOf("series", Series, default=Series)
    limits = InstanceOf("limits", Limits, default=Limits)

    def __init__(self, ts=None, result=None, code=None, dimensions=None):
        if dimensions is None:
            dimensions = []

        if ts is None:
            ts = local_now()

        self.ts = ts
        self.result = result
        self.code = code
        self.series = Series(*dimensions)

    def add_sample(self, ts, **kwargs):
        """Add a sample to this measurements."""
        if not self.series.offsets:
            self.ts = ts
            offset = 0
        else:
            dt = ts - self.ts
            offset = (dt.days * 24 * 60 * 60 * 1000 + dt.seconds * 1000 +
                      dt.microseconds // 1000)
        self.series.add_sample(offset, **kwargs)

    def samples(self):
        """Yield samples as dictionaries, keyed by dimensions."""
        names = self.series.dimensions
        for n, offset in enumerate(self.series.offsets):
            dt = datetime.timedelta(microseconds=offset * 1000)
            d = {"ts": self.ts + dt}
            for name in names:
                d[name] = getattr(self.series, name)[n]
            yield d


class Part(Object):
    """Contains information regarding the part which this payload relates
    to.
    """
    partTypeID = String("partTypeID")
    partID = String("partID", 256)
    result = Result()
    code = Code()
    metaData = Map("metaData")

    def __init__(self,
                 partTypeID=None,
                 partID=None,
                 result=None,
                 code=None,
                 **metaData):
        self.partTypeID = partTypeID
        self.partID = partID
        self.result = result
        self.code = code
        if metaData:
            self.metaData.update(metaData)


@payload_wrapper
class MeasurementPayload(Object):
    """The measurement message is the format to exchange simple
    (non-structured, non-complex ) measurement data. It also allows to
    transport multiple measurement data (eg. values over time), called
    'series'.
    """
    CONTENT_SPEC = "urn:spec://eclipse.org/unide/measurement-message#v2"
    device = InstanceOf("device", Device)
    part = InstanceOf("part", Part)
    measurements = ListOf("measurements", Measurement)

    def __init__(self, device, part=None, measurements=None):
        if not measurements:
            measurements = []

        self._data["content-spec"] = self.CONTENT_SPEC
        self.device = device
        self.part = part
        self.measurements = measurements


def device_measurement(device,
                       ts=None,
                       part=None,
                       result=None,
                       code=None,
                       **kwargs):
    """Returns a JSON MeasurementPayload ready to be send through a
    transport.

    If `ts` is not given, the current time is used. `part` is an
    optional `Part` object, and `result` and `code` are the respective
    fields of the `Measurement` object. All other arguments are
    interpreted as dimensions.

    Minimal example, using a `Device` object to send two
    measurements:

    >>> d = Device("12345")
    >>> def publish(msg):
    ...     pass
    >>> publish(d.measurement(temperature=22.8))
    >>> publish(d.measurement(pressure=4.1))

    """
    if ts is None:
        ts = local_now()

    payload = MeasurementPayload(device=device, part=part)
    m = Measurement(ts, result, code, list(kwargs))
    payload.measurements.append(m)
    m.add_sample(ts, **kwargs)
    return dumps(payload)


# Attach `measurement` to the Device class
Device.measurement = device_measurement
