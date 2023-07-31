"""
Debug Adapter Protocol Interface

Translated to Python from [DAP specification](https://microsoft.github.io/debug-adapter-protocol/specification)
"""
from __future__ import annotations

from typing import Any, Literal, TypedDict

from typing_extensions import NotRequired


class _ProtocolMessage(TypedDict):
    """ Base class of requests, responses, and events. """
    seq: int


class _UnvalidatedProtocolMessage(_ProtocolMessage):
    type: str


class _Request(_ProtocolMessage):
    """ A client or debug adapter initiated request. """
    type: Literal["request"]


class _UnvalidatedRequest(_Request):
    command: str

    arguments: NotRequired[Any]


class Event(_ProtocolMessage):
    type: Literal["event"]

    event: str

    body: NotRequired[Any]


class _Response(_ProtocolMessage):
    type: Literal["response"]

    request_seq: int

    success: bool

    command: str

    message: NotRequired[Literal["cancelled", "notStopped"] | str]


class Response(_Response):
    """ Response for a request. """
    body: NotRequired[Any]


class ErrorResponse(_Response):
    """ On error (whenever success is false), the body can provide more details. """
    body: NotRequired[Message]


class Message:
    """ A structured message object. Used to return errors from requests. """
    id: str
    format: str
    # variables: NotRequired[...]
    # sendTelemetry: NotRequired[bool]
    # showUser: NotRequired[bool]
    # url: NotRequired[str]
    # urlLabel: NotRequired[str]


##################
### Initialize ###
##################

class InitializeRequest(_Request):
    command: Literal["initialize"]

    arguments: InitializeRequestArguments


class InitializeRequestArguments(TypedDict):
    clientID: NotRequired[str]

    clientName: NotRequired[str]

    adapterID: NotRequired[str]

    locale: NotRequired[str]

    linesStartAt1: NotRequired[bool]
    columnsStartAt1: NotRequired[bool]
    pathFormat: NotRequired[Literal["path", "uri"] | str]
    supportsVariableType: NotRequired[bool]

    # supportsVariablePaging: NotRequired[bool]
    # supportsRunInTerminalRequest: NotRequired[bool]
    # supportsMemoryReferences: NotRequired[bool]
    # supportsProgressReporting: NotRequired[bool]
    # supportsInvalidatedEvent: NotRequired[bool]
    # supportsMemoryEvent: NotRequired[bool]
    # supportsArgsCanBeInterpretedByShell: NotRequired[bool]
    # supportsStartDebuggingRequest: NotRequired[bool]


class InitializeResponse(_Response):
    body: NotRequired[Capabilities]


class Capabilities(TypedDict):
    supportsConfigurationDoneRequest: NotRequired[bool]
    # supportsFunctionBreakpoints: NotRequired[bool]
    # supportsConditionalBreakpoints: NotRequired[bool]
    # supportsHitConditionalBreakpoints: NotRequired[bool]
    # supportsEvaluateForHovers: NotRequired[bool]
    # exceptionBreakpointFilters: NotRequired[ExceptionBreakpointsFilter[]]
    # supportsStepBack: NotRequired[bool]
    # supportsSetVariable: NotRequired[bool]
    # supportsRestartFrame: NotRequired[bool]
    # supportsGotoTargetsRequest: NotRequired[bool]
    # supportsStepInTargetsRequest: NotRequired[bool]
    # supportsCompletionsRequest: NotRequired[bool]
    # completionTriggerCharacters: NotRequired[List[str]]
    # supportsModulesRequest: NotRequired[bool]
    # additionalModuleColumns: NotRequired[ColumnDescriptor[]]
    # supportedChecksumAlgorithms: NotRequired[ChecksumAlgorithm[]]
    # supportsRestartRequest: NotRequired[bool]
    # supportsExceptionOptions: NotRequired[bool]
    # supportsValueFormattingOptions: NotRequired[bool]
    # supportsExceptionInfoRequest: NotRequired[bool]
    # supportTerminateDebuggee: NotRequired[bool]
    # supportSuspendDebuggee: NotRequired[bool]
    # supportsDelayedStackTraceLoading: NotRequired[bool]
    # supportsLoadedSourcesRequest: NotRequired[bool]
    # supportsLogPoints: NotRequired[bool]
    # supportsTerminateThreadsRequest: NotRequired[bool]
    # supportsSetExpression: NotRequired[bool]
    # supportsTerminateRequest: NotRequired[bool]
    # supportsDataBreakpoints: NotRequired[bool]
    # supportsReadMemoryRequest: NotRequired[bool]
    # supportsWriteMemoryRequest: NotRequired[bool]
    # supportsDisassembleRequest: NotRequired[bool]
    # supportsCancelRequest: NotRequired[bool]
    # supportsBreakpointLocationsRequest: NotRequired[bool]
    # supportsClipboardContext: NotRequired[bool]
    # supportsSteppingGranularity: NotRequired[bool]
    # supportsInstructionBreakpoints: NotRequired[bool]
    # supportsExceptionFilterOptions: NotRequired[bool]
    # supportsSingleThreadExecutionRequests: NotRequired[bool]


##############
### Launch ###
##############

class LaunchRequest(_Request):
    command: Literal["launch"]
    arguments: LaunchRequestArguments


class LaunchRequestArguments(TypedDict):
    noDebug: NotRequired[bool]

    __restart: NotRequired[Any]


Request = InitializeRequest | LaunchRequest
UnvalidatedRequest = Request | _UnvalidatedRequest


ProtocolMessage = Request | Response | Event
UnvalidatedProtocolMessage = ProtocolMessage | _UnvalidatedProtocolMessage
