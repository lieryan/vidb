import asyncio

from tests.stubs import DAPServerMixin


INITIALIZE_RESPONSE = {
    "seq": 1,
    "type": "response",
    "request_seq": 1,
    "success": True,
    "command": "initialize",
    "body": {
        "supportsCompletionsRequest": True,
        "supportsConditionalBreakpoints": True,
        "supportsConfigurationDoneRequest": True,
        "supportsDebuggerProperties": True,
        "supportsDelayedStackTraceLoading": True,
        "supportsEvaluateForHovers": True,
        "supportsExceptionInfoRequest": True,
        "supportsExceptionOptions": True,
        "supportsFunctionBreakpoints": True,
        "supportsHitConditionalBreakpoints": True,
        "supportsLogPoints": True,
        "supportsModulesRequest": True,
        "supportsSetExpression": True,
        "supportsSetVariable": True,
        "supportsValueFormattingOptions": True,
        "supportsTerminateRequest": True,
        "supportsGotoTargetsRequest": True,
        "supportsClipboardContext": True,
        "exceptionBreakpointFilters": [
            {
                "filter": "raised",
                "label": "Raised Exceptions",
                "default": False,
                "description": "Break whenever any exception is raised.",
            },
            {
                "filter": "uncaught",
                "label": "Uncaught Exceptions",
                "default": True,
                "description": "Break when the process is exiting due to unhandled exception.",
            },
            {
                "filter": "userUnhandled",
                "label": "User Uncaught Exceptions",
                "default": False,
                "description": "Break when exception escapes into library code.",
            },
        ],
        "supportsStepInTargetsRequest": True,
    },
}

INITIALIZED_EVENT = {
    "seq": 2,
    "type": "event",
    "event": "initialized",
}

CONFIGURATION_DONE_RESPONSE = {
    "seq": 3,
    "type": "response",
    "request_seq": 3,
    "success": True,
    "command": "configurationDone",
}

ATTACH_RESPONSE = {
    "seq": 4,
    "type": "response",
    "request_seq": 2,
    "success": True,
    "command": "attach",
}


class TestInitialize(DAPServerMixin):
    async def test_attach_initialize_sequence(self, client):
        async def server_initialize():
            async with self.assert_request_response(
                "initialize", response=INITIALIZE_RESPONSE
            ) as initialize_request:
                pass

            async with self.assert_request_response(
                "attach", response=ATTACH_RESPONSE
            ) as attach_request:
                self.send_message(INITIALIZED_EVENT)

                async with self.assert_request_response(
                    "configurationDone", response=CONFIGURATION_DONE_RESPONSE
                ) as configuration_done_request:
                    pass

        await asyncio.gather(
            server_initialize(),
            client.initialize(),
        )
