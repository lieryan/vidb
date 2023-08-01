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


################
## Initialize ##
################

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


########################
## Configuration Done ##
########################

class ConfigurationDoneRequest(_Request):
    command: Literal["configurationDone"]

    arguments: NotRequired[ConfigurationDoneArguments]


class ConfigurationDoneArguments(TypedDict):
    pass


############
## Launch ##
############

class LaunchRequest(_Request):
    command: Literal["launch"]
    arguments: LaunchRequestArguments


class LaunchRequestArguments(TypedDict):
    noDebug: NotRequired[bool]

    __restart: NotRequired[Any]


############
## Attach ##
############


class AttachRequest(_Request):
    command: Literal["attach"]
    arguments: AttachRequestArguments


class AttachRequestArguments(TypedDict):
    __restart: NotRequired[Any]


#############
## Threads ##
#############


class ThreadsRequest(_Request):
    command: Literal["threads"]


class ThreadsResponse(_Response):
    body: _ThreadsResponseBody


class _ThreadsResponseBody(TypedDict):
    threads: list[Thread]


################
## StackTrace ##
################


class StackTraceRequest(_Request):
    command: Literal["stackTrace"]

    arguments: StackTraceArguments


class StackTraceArguments(TypedDict):
    threadId: int

    # startFrame: NotRequired[int]
    # levels: NotRequired[int]
    # format: NotRequired[StackFrameFormat]  # requires supportsValueFormattingOptions


class StackTraceResponse(_Response):
    body: _ThreadsResponseBody


class _StackTraceResponseBody(TypedDict):
    stackFrames: list[StackFrame]
    # totalFrames: NotRequired[int]


###########
## Types ##
###########

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


class Thread(TypedDict):
    id: int
    name: str


class Source(TypedDict):
    name: NotRequired[str]
    path: NotRequired[str]
    # sourceReference: NotRequired[int]
    # presentationHint: NotRequired[Literal['normal', 'emphasize', 'deemphasize']]
    # origin: NotRequired[str]
    # sources: NotRequired[list[Source]]
    # adapterData: NotRequired[Any]
    # checksums: NotRequired[list[Checksum]]


class StackFrame(TypedDict):
    id: int
    name: str

    # source: NotRequired[Source]
    # line: int
    # column: int
    # endLine: NotRequired[int]
    # endColumn: NotRequired[int]

    # canRestart: NotRequired[bool]  # requires supportsRestartRequest
    # instructionPointerReference: NotRequired[str]
    # moduleId: NotRequired[int | str]
    # presentationHint: NotRequired[Literal['normal', 'label', 'subtle']]


Request = InitializeRequest | LaunchRequest | AttachRequest | ConfigurationDoneRequest | ThreadsRequest | StackTraceRequest
UnvalidatedRequest = Request | _UnvalidatedRequest


ProtocolMessage = Request | Response | Event
UnvalidatedProtocolMessage = ProtocolMessage | _UnvalidatedProtocolMessage
