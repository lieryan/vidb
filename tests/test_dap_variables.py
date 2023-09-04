import asyncio

from tests.stubs import DAPServerMixin


class TestVariables(DAPServerMixin):
    async def test_attach_variables(self, client):
        async def server_initialize():
            async with self.assert_request_response("initialize", response=INITIALIZE_RESPONSE):
                pass

            async with self.assert_request_response("attach", response=ATTACH_RESPONSE):
                self.send_message(INITIALIZED_EVENT)

                async with self.assert_request_response(
                    "configurationDone", response=CONFIGURATION_DONE_RESPONSE
                ):
                    pass

        await asyncio.gather(
            server_initialize(),
            client.initialize(),
        )
