"""
Debug Adapter Protocol Interface

Translated to Python from [DAP specification](https://microsoft.github.io/debug-adapter-protocol/specification)
"""
from __future__ import annotations

from typing import (
    Any,
    Literal,
    Optional,
    TypedDict,
)


class _ProtocolMessage(TypedDict):
    seq: int


class ProtocolMessage(_ProtocolMessage):
    """ Base class of requests, responses, and events. """
    type: Literal["request", "response", "event"] | str


class _Request(_ProtocolMessage):
    """ A client or debug adapter initiated request. """
    type: Literal["request"]


class Request(_Request):
    command: str

    arguments: Optional[Any]


class Event(_ProtocolMessage):
    type: Literal["event"]

    event: str

    body: Optional[Any]


class _Response(_ProtocolMessage):
    type: Literal["response"]

    request_seq: int

    success: bool

    command: str

    message: Optional[Literal["cancelled"] | str]


class Response(_Response):
    """ Response for a request. """
    body: Optional[Any]


class ErrorResponse(_Response):
    """ On error (whenever success is false), the body can provide more details. """
    body: Optional[Message]


class Message:
    """ A structured message object. Used to return errors from requests. """
    id: str
    format: str
    # variables: Optional[...]
    # sendTelemetry: Optional[bool]
    # showUser: Optional[bool]
    # url: Optional[str]
    # urlLabel: Optional[str]
