import pytest

from src.client import IrcClient


@pytest.fixture(scope="function")
def irc_client(
    mock_update_channels_func,
    mock_update_members_func,
    mock_receiving_message_func,
):
    return IrcClient(
        'testhost',
        '6667',
        'nick',
        'utf-8',
        mock_update_channels_func[0],
        mock_update_members_func[0],
        mock_receiving_message_func[0],
    )


@pytest.fixture(scope='package')
def mock_update_channels_func():
    log = []

    async def on_update_channels(param):
        log.append(param)

    return on_update_channels, log


@pytest.fixture(scope='package')
def mock_update_members_func():
    log = []

    async def on_update_members(param):
        log.append(param)

    return on_update_members, log


@pytest.fixture(scope='package')
def mock_receiving_message_func():
    log = []

    async def on_receiving_message(param):
        log.append(param)

    return on_receiving_message, log
