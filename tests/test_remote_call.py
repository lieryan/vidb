import asyncio
import pytest

from tests.stubs import DAPServerMixin


class TestRemoteCall(DAPServerMixin):
    async def test_successful_remote_call(self, client):
        async def server():
            RESPONSE = {
                "seq": 1,
                "type": "response",
                "success": True,
                "command": "helloworld",
                "request_seq": 1,
            }
            async with self.assert_request_response("helloworld", response=RESPONSE):
                pass

        await asyncio.gather(
            server(),
            client.remote_call(
                dict,
                command="helloworld",
                arguments={
                    "hello": "world",
                },
            ),
        )

    async def test_failed_remote_call(self, client):
        async def server():
            RESPONSE = {
                "seq": 1,
                "type": "response",
                "success": False,
                "command": "helloworld",
                "request_seq": 1,
                "message": "exception message from server",
            }
            async with self.assert_request_response("helloworld", response=RESPONSE):
                pass

        asyncio.create_task(server())
        with pytest.raises(Exception, match="exception message from server"):
            await client.remote_call(
                dict,
                command="helloworld",
                arguments={
                    "hello": "world",
                },
            )
