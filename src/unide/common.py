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

"""Commonly used entities and properties in all PPMP messages."""

from .schema import String, Object, Map


def Code(null=True):
    """The code is an addendum to the result which allows to pass
    information in the case the result was NOK.  The value often stems
    from the integrated system e.g. a PLC.
    """
    return String("code", 36, null=null)


def DeviceID(null=False):
    """The unique ID of the device. As this is used to identify a device
    independently from time or location. The ID itself must be stable
    and unique. The recommendation is to use a universally unique
    identifier (UUID). Reprentation could follow GIAI, UUID or
    others.
    """
    return String("deviceID", 36, null=null)


def Result():
    """Information if the quality of the produced part was ok or
    not. Possible values: 'UNKNOWN', 'OK' or 'NOK'. Default value is
    'UNKNOWN'
    """
    return String("result", oneof=('OK', 'NOK', 'UNKNOWN'))


class Device(Object):
    """Contains information about the device.

    :param string[36] deviceID: The unique ID of the device. As this
           is used to identify a device independently from time or
           location. The ID itself must be stable and unique. The
           recommendation is to use a universally unique identifier
           (UUID). Required. Representation could follow GIAI, UUID or
           others.

    :param string operationalStatus: The operationalStatus describes
           the status or mode of a device. Optional.

    :param Map<String,String> metaData: Additional key-value pairs in
           a JSON structure format. Key and value must be strings. Subfields
           can be any key/string value pair.

    Example:

    >>> from pyppmp.measurement import Device
    >>> device = Device("0910298309812398")
    >>> print device.deviceID
    0910298309812398

    """
    deviceID = DeviceID()
    operationalStatus = String("operationalStatus")
    metaData = Map("metaData")

    def __init__(self, deviceID, operationalStatus=None, **metaData):
        self.deviceID = deviceID
        self.operationalStatus = operationalStatus
        if metaData:
            self.metaData.update(metaData)
