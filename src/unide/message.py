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

"""The main purpose of the machine message format is to allow devices
and integrators to send messages containing an interpretation of
measurement data or status."""

from .util import payload_wrapper, dumps, local_now
from .schema import Object, String, Datetime, Map, InstanceOf, ListOf
from .common import Device, Code


def MessageType():
    """The type of message. Either 'DEVICE' or 'TECHNICAL_INFO'."""
    return String("type", oneof=('DEVICE', 'TECHNICAL_INFO'))


def Severity():
    """Severity of the message. Possible values: 'HIGH' 'MEDIUM' 'LOW'
    'UNKNOWN'
    """
    return String("severity", oneof=('HIGH', 'MEDIUM', 'LOW', 'UNKNOWN'))


class Message(Object):
    # pylint: disable=too-many-instance-attributes
    """A machine message.

    :param string origin: The origin of the message if not the device
        identified by deviceID in the header element.  Could be used
        to identify a subsystem or a particular sensor/part of the
        device where the message actually relates to.

    :param enum type: The type of message. Default is DEVICE but can
        be set to TECHNICAL_INFO indicating a problem with the
        integration of the actual device. Possible values: "DEVICE"
        "TECHNICAL_INFO"

    :param enum severity: Severity of the message. Possible values:
        "HIGH" "MEDIUM" "LOW" "UNKNOWN"


    :param string(36) code: Code identifying the problem described in
        the message. Required.  The value often stems from the machine
        e.g. a PLC code. Is similar to code in measurement interface.

    :param string(1000) title: The title of the message

    :param string(2000) description: The description is used to
        describe the purpose of the message, e.g. the problem


    :param string(2000) hint: In case a problem is reported, the hint
        can be used to point out a possible solution.

    """
    ts = Datetime("ts")
    origin = String("origin")
    type = MessageType()
    severity = Severity()
    code = Code(null=False)
    title = String("title", 1000)
    description = String("description", 2000)
    hint = String("hint", 2000)
    metaData = Map("metaData")

    def __init__(self,
                 code,
                 ts=None,
                 origin=None,
                 type=None,
                 severity=None,
                 title=None,
                 description=None,
                 hint=None,
                 **metaData):
        # pylint: disable=redefined-builtin, too-many-arguments
        self.ts = ts
        self.code = code
        self.origin = origin
        self.type = type
        self.severity = severity
        self.title = title
        self.description = description
        self.hint = hint
        if metaData:
            self.metaData.update(metaData)


@payload_wrapper
class MessagePayload(Object):
    """The main purpose of the machine message format is to allow devices
    and integrators to send messages containing an interpretation of
    measurement data or status."""
    CONTENT_SPEC = "urn:spec://eclipse.org/unide/machine-message#v2"
    device = InstanceOf("device", Device)
    messages = ListOf("messages", Message)

    def __init__(self, device):
        self._data["content-spec"] = self.CONTENT_SPEC
        self.device = device


def device_message(device,
                   code,
                   ts=None,
                   origin=None,
                   type=None,
                   severity=None,
                   title=None,
                   description=None,
                   hint=None,
                   **metaData):
    # pylint: disable=redefined-builtin, too-many-arguments
    """This quickly builds a time-stamped message. If `ts` is None, the
    current time is used.
    """
    if ts is None:
        ts = local_now()
    payload = MessagePayload(device=device)
    payload.messages.append(
        Message(
            code=code,
            ts=ts,
            origin=origin,
            type=type,
            severity=severity,
            title=title,
            description=description,
            hint=hint,
            **metaData))
    return dumps(payload)


Device.message = device_message
