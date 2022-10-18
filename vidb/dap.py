"""
Debug Adapter Protocol Interface

Translated to Python from [DAP specification](https://microsoft.github.io/debug-adapter-protocol/specification)
"""
from __future__ import annotations

from typing import (
    Any,
    List,
    Literal,
    Optional,
    TypedDict,
)


class _ProtocolMessage(TypedDict):
    """ Base class of requests, responses, and events. """
    seq: int


class _UnvalidatedProtocolMessage(_ProtocolMessage):
    type: str


class _Request(_ProtocolMessage):
    """ A client or debug adapter initiated request. """
    type: Literal["request"]


class _UnvalidatedRequest(_Request):
    pass
    # command: str
    # arguments: Optional[Any]


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


class InitializeRequest(_Request):
    command: Literal["initialize"]

    arguments: InitializeRequestArguments


class InitializeRequestArguments(TypedDict):
    clientID: Optional[str]

    clientName: Optional[str]

    adapterID: Optional[str]

    locale: Optional[str]

    # linesStartAt1: Optional[bool]
    # columnsStartAt1: Optional[bool]
    # pathFormat: Optional[Literal["path", "uri"] | str]

    # supportsVariableType: Optional[bool]
    # supportsVariablePaging: Optional[bool]
    # supportsRunInTerminalRequest: Optional[bool]
    # supportsMemoryReferences: Optional[bool]
    # supportsProgressReporting: Optional[bool]
    # supportsInvalidatedEvent: Optional[bool]
    # supportsMemoryEvent: Optional[bool]
    # supportsArgsCanBeInterpretedByShell: Optional[bool]


class InitializeResponse(_Response):
    body: Capabilities


class Capabilities(TypedDict):
    pass
    # supportsConfigurationDoneRequest: Optional[bool]
    # supportsFunctionBreakpoints: Optional[bool]
    # supportsConditionalBreakpoints: Optional[bool]
    # supportsHitConditionalBreakpoints: Optional[bool]
    # supportsEvaluateForHovers: Optional[bool]
    # exceptionBreakpointFilters: Optional[ExceptionBreakpointsFilter[]]
    # supportsStepBack: Optional[bool]
    # supportsSetVariable: Optional[bool]
    # supportsRestartFrame: Optional[bool]
    # supportsGotoTargetsRequest: Optional[bool]
    # supportsStepInTargetsRequest: Optional[bool]
    # supportsCompletionsRequest: Optional[bool]
    # completionTriggerCharacters: Optional[List[str]]
    # supportsModulesRequest: Optional[bool]
    # additionalModuleColumns: Optional[ColumnDescriptor[]]
    # supportedChecksumAlgorithms: Optional[ChecksumAlgorithm[]]
    # supportsRestartRequest: Optional[bool]
    # supportsExceptionOptions: Optional[bool]
    # supportsValueFormattingOptions: Optional[bool]
    # supportsExceptionInfoRequest: Optional[bool]
    # supportTerminateDebuggee: Optional[bool]
    # supportSuspendDebuggee: Optional[bool]
    # supportsDelayedStackTraceLoading: Optional[bool]
    # supportsLoadedSourcesRequest: Optional[bool]
    # supportsLogPoints: Optional[bool]
    # supportsTerminateThreadsRequest: Optional[bool]
    # supportsSetExpression: Optional[bool]
    # supportsTerminateRequest: Optional[bool]
    # supportsDataBreakpoints: Optional[bool]
    # supportsReadMemoryRequest: Optional[bool]
    # supportsWriteMemoryRequest: Optional[bool]
    # supportsDisassembleRequest: Optional[bool]
    # supportsCancelRequest: Optional[bool]
    # supportsBreakpointLocationsRequest: Optional[bool]
    # supportsClipboardContext: Optional[bool]
    # supportsSteppingGranularity: Optional[bool]
    # supportsInstructionBreakpoints: Optional[bool]
    # supportsExceptionFilterOptions: Optional[bool]
    # supportsSingleThreadExecutionRequests: Optional[bool]


Request = InitializeRequest
UnvalidatedRequest = Request | _UnvalidatedProtocolMessage


ProtocolMessage = Request | Response | Event
UnvalidatedProtocolMessage = ProtocolMessage | _UnvalidatedProtocolMessage
