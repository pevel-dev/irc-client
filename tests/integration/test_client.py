import asyncio

import pytest


@pytest.mark.asyncio
@pytest.mark.client
async def test_connect_server(irc_client_for_server, irc_server, mock_receiving_message_func):
    await irc_client_for_server.connect()
    loop = asyncio.get_event_loop()
    loop.create_task(irc_client_for_server.handle())

    await asyncio.sleep(5)

    assert len(mock_receiving_message_func[1]) > 0
