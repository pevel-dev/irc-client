import threading
import time

import irc.server
import pytest

from src.client import IrcClient

run_server = None


def server_task(channels):
    server = irc.server.IRCServer(('127.0.0.1', 6667), irc.server.IRCClient)
    server.channels = channels
    global run_server
    run_server = server
    server.serve_forever()


@pytest.fixture(scope="package")
def irc_server(irc_channels):
    thread = threading.Thread(target=server_task, args=(irc_channels,))
    thread.start()
    yield thread
    run_server.shutdown()
    # server.shutdown()


@pytest.fixture(scope="package")
def irc_channels() -> dict[str, irc.server.IRCChannel]:
    channel_1 = irc.server.IRCChannel(name="Test Channel 1", topic="Test Channel 1 topic")
    channel_2 = irc.server.IRCChannel(name="Test Channel 2", topic="Test Channel 3 topic")
    channel_3 = irc.server.IRCChannel(name="Test Channel 3", topic="Test Channel 3 topic")
    return {'Test1': channel_1, 'Test2': channel_2, 'Test3': channel_3}


@pytest.fixture(scope="function")
def irc_client_for_server(
        mock_update_channels_func,
        mock_update_members_func,
        mock_receiving_message_func,
):
    return IrcClient(
        '127.0.0.1',
        '6667',
        'nick',
        'cp1251',
        mock_update_channels_func[0],
        mock_update_members_func[0],
        mock_receiving_message_func[0],
    )
