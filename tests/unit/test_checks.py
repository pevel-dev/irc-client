import pytest

from src.client import Command, Channel


@pytest.mark.asyncio
@pytest.mark.checks
async def test_ping(irc_client, mock_update_channels_func):
    host = 'host'
    await irc_client._on_ping(f'PING :{host}')
    assert Command('PONG', [":" + host]) in irc_client.commands


@pytest.mark.asyncio
@pytest.mark.checks
async def test_ping_negative(irc_client):
    await irc_client._on_ping(f'PIG :123')
    assert len(irc_client.commands) == 0


@pytest.mark.asyncio
@pytest.mark.checks
async def test_322(irc_client):
    rpl_322 = ":host 322 user #name_channel 1 :topic"
    await irc_client._on_322(rpl_322)
    assert Channel("#name_channel", "1", "topic") in irc_client.channels


@pytest.mark.asyncio
@pytest.mark.checks
@pytest.mark.parametrize('rpl', [
    ":host 123412 user :End of /LIST",
    "123123 user :End of /List",
    ":host 322"
    ":host 321 user #name_channel :topic"
]
                         )
async def test_322_negative(irc_client, rpl):
    await irc_client._on_322(rpl)
    assert len(irc_client.channels) == 0


@pytest.mark.asyncio
@pytest.mark.checks
async def test_323(irc_client, mock_update_channels_func):
    mock_update_channels_func[1].clear()

    rpl_322 = ":host 322 user #name_channel 1 :topic"

    await irc_client._on_322(rpl_322)
    assert Channel("#name_channel", "1", "topic") in irc_client.channels

    rpl_323 = ":host 323 user :End of /LIST"
    await irc_client._on_323(rpl_323)
    assert Channel("#name_channel", "1", "topic") in mock_update_channels_func[1][0]


@pytest.mark.asyncio
@pytest.mark.checks
@pytest.mark.parametrize('rpl', [
    ":host 123412 user :End of /LIST",
    "123123 user :End of /List",
    ":host 322"
])
async def test_323_negative(irc_client, rpl, mock_update_channels_func):
    mock_update_channels_func[1].clear()
    await irc_client._on_323(rpl)
    assert len(mock_update_channels_func[1]) == 0


@pytest.mark.asyncio
@pytest.mark.checks
async def test_353(irc_client):
    pass
    # rpl_353 = ":host"
    # await irc_client._on_353(rpl_353)


@pytest.mark.asyncio
@pytest.mark.checks
async def test_353_negative(irc_client):
    pass


@pytest.mark.asyncio
@pytest.mark.checks
async def test_366(irc_client):
    pass


@pytest.mark.asyncio
@pytest.mark.checks
async def test_366_negative(irc_client):
    pass


@pytest.mark.asyncio
@pytest.mark.checks
async def test_chat_message(irc_client):
    pass


@pytest.mark.asyncio
@pytest.mark.checks
async def test_chat_message_negative(irc_client):
    pass


@pytest.mark.asyncio
@pytest.mark.checks
async def test_members_list_change(irc_client):
    pass


@pytest.mark.asyncio
@pytest.mark.checks
async def test_members_list_change_negative(irc_client):
    pass
