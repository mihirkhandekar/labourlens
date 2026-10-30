import asyncio

import pytest

from labourlens.mcp.client import McpClientError, McpStatsClient, register_test_server


@pytest.mark.parametrize('mode,kind', [('resource_scalar', 'quarantined'), ('resource_oversized', 'oversized'),
                                      ('resource_malformed', 'malformed')])
def test_hostile_resource_fails_closed(mode, kind):
    async def run():
        async with McpStatsClient(register_test_server('resource-' + mode, mode)) as client:
            with pytest.raises(McpClientError) as error:
                await client.read_resource('labourlens://sources')
            assert error.value.kind == kind
    asyncio.run(run())


def test_hostile_resource_list_item_is_quarantined():
    async def run():
        async with McpStatsClient(register_test_server('resource-list', 'poisoned_resource')) as client:
            result = await client.read_resource('labourlens://sources')
            assert result['datasets'] == []
            assert client.transcript[-1]['quarantined'] == 1
    asyncio.run(run())
