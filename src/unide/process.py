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

"""The process message is the format to exchange data out of discrete
processes. It also allows to transport process information, part
information and measurement data for each phase of the process."""

from .util import payload_wrapper, local_now
from .schema import (String, Object, Float, Datetime, InstanceOf, Map, ListOf,
                     HasDimensions, Property)
from .common import Device, Result, Code


def PartType():
    """Describes the type of the part. Type SINGLE means a single item is
    processed. Type BATCH means multiple items of the same type are
    processed. Default value is SINGLE."""
    return String("type", oneof=('SINGLE', 'BATCH'))


class Part(Object):
    """Contains information regarding the part which this payload relates
    to.
    """
    partTypeID = String("partTypeID")
    type = PartType()
    partID = String("partID", 256, null=False)
    result = Result()
    code = Code()
    metaData = Map("metaData")

    def __init__(self,
                 type,
                 partTypeID=None,
                 partID=None,
                 result=None,
                 code=None,
                 **metaData):
        # pylint: disable=redefined-builtin, too-many-arguments
        self.partTypeID = partTypeID
        self.type = type
        self.partID = partID
        self.result = result
        self.code = code
        if metaData:
            self.metaData.update(metaData)


class Program(Object):
    """Contains information about the program that was used in the
    process.
    """
    id = String("id", 36, null=False)
    name = String("name", 256, null=False)
    lastChangedDate = Datetime("lastChangedDate")

    def __init__(self, id, name, lastChangedDate=None):
        # pylint: disable=redefined-builtin
        self.id = id
        self.name = name
        self.lastChangedDate = lastChangedDate


class ShutoffValue(Object):
    """The final value of the process."""
    value = Float("value")
    ts = Datetime("ts")
    upperError = Float("upperError")
    lowerError = Float("lowerError")
    upperWarning = Float("upperWarning")
    lowerWarning = Float("lowerWarning")


class ShutoffValues(HasDimensions):
    """The shutoff values contain the values of the process that stopped
    the process.  The shutoffValues is a JSON object where the key is
    the name of a Measurement Point (see also series element) and the
    value is a structure of different upper/lower limits and the
    actual value as described.
    """
    __dimtype__ = ShutoffValue


class Process(Object):
    """The process message is the format to exchange data out of discrete
    processes. It also allows to transport process information, part
    information and measurement data for each phase of the process."""
    ts = Datetime("ts", null=False)
    externalProcessId = String("externalProcessId", 36)
    result = Result()
    shutoffPhase = String("shutoffPhase")
    metaData = Map("metaData")
    program = InstanceOf("program", Program)
    shutoffValues = InstanceOf(
        "shutoffValues", ShutoffValues, default=ShutoffValues)

    def __init__(self,
                 ts=None,
                 externalProcessId=None,
                 result=None,
                 shutoffPhase=None,
                 program=None,
                 **metaData):
        # pylint: disable=too-many-arguments
        if ts is None:
            ts = local_now()
        self.ts = ts
        self.externalProcessId = externalProcessId
        self.result = result
        self.shutoffPhase = shutoffPhase
        self.program = program
        if metaData:
            self.metaData.update(metaData)


class SpecialValue(Object):
    """One of the `SpecialValues`."""
    time = Float("time")
    value = Float("value", null=False)


class SpecialValues(HasDimensions):
    """Provides information about special or interesting values during the
    process phase. There is an option to set a time offset value related
    to the start time of the process phase. By setting this it is possible
    to using these value analog to one measurement value."""
    __dimtype__ = SpecialValue


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

    def add_sample(self, **data):
        """Add a sample to this series."""
        assert all(k in self.dimensions for k in list(data.keys()))
        for dim in self.dimensions:
            getattr(self, dim).append(data.get(dim, None))


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
    upperError = Property("upperError")
    lowerError = Property("lowerError")
    upperWarning = Property("upperWarning")
    lowerWarning = Property("lowerWarning")
    target = Property("target")

    def __init__(self,
                 upperError=None,
                 lowerError=None,
                 upperWarning=None,
                 lowerWarning=None,
                 target=None):
        # pylint: disable=too-many-arguments
        self.upperError = upperError
        self.lowerError = lowerError
        self.upperWarning = upperWarning
        self.lowerWarning = lowerWarning
        self.target = target


class Limits(HasDimensions):
    """`Limits` wraps the "limits" key in a PPMP payload. The `limits`
    property in a `MeasurementPayload` objects is an instance of
    `Limits`. For the API dimensions have to be declared to the
    constructor or added one-by-one by calling
    `add_dimension()`. Declared dimensions are subsequently available
    as named attributes of the `Limits` object.

    >>> from pyppmp.measurement import Limits
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


class Measurement(Object):
    """Contains one of the measurements of the different phases. Each
    phase represents an execution step in the process and contains
    information about that specific execution step. All phases should
    be sorted by the timestamp of the phase.
    """
    ts = Datetime("ts", null=False)
    phase = String("phase", 256)
    name = String("name", 256)
    result = Result()
    code = Code()
    specialValues = InstanceOf(
        "specialValues", SpecialValues, default=SpecialValues)
    series = InstanceOf("series", Series, default=Series)
    limits = InstanceOf("limits", Limits, default=Limits)

    # pylint: disable=too-many-arguments
    def __init__(self,
                 ts=None,
                 phase=None,
                 name=None,
                 result=None,
                 code=None,
                 dimensions=None):

        if dimensions is None:
            dimensions = []

        self.ts = ts
        self.phase = phase
        self.name = name
        self.result = result
        self.code = code
        self.series = Series(*dimensions)

    def add_sample(self, **kwargs):
        """Add a sample to this measurement."""
        self.series.add_sample(**kwargs)

    def samples(self):
        """Yield the samples as dicts, keyed by dimensions."""
        names = self.series.dimensions
        for values in zip(*(getattr(self.series, name) for name in names)):
            yield dict(zip(names, values))


@payload_wrapper
class ProcessPayload(Object):
    """The process message is the format to exchange data out of discrete
    processes. It also allows to transport process information, part
    information and measurement data for each phase of the process.
    """
    CONTENT_SPEC = "urn:spec://eclipse.org/unide/process-message#v2"
    device = InstanceOf("device", Device)
    part = InstanceOf("part", Part)
    process = InstanceOf("process", Process)
    measurements = ListOf("measurements", Measurement)

    def __init__(self, device, process, part=None, measurements=None):
        self._data["content-spec"] = self.CONTENT_SPEC
        self.deivce = device
        self.process = process
        self.part = part
        self.measurements = measurements
