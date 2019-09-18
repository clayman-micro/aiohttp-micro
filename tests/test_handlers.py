async def test_meta_endpoint(aiohttp_client, app):
    client = await aiohttp_client(app)

    resp = await client.get("/-/meta")

    assert resp.status == 200


async def test_health_endpoint(aiohttp_client, app):
    client = await aiohttp_client(app)

    resp = await client.get("/-/health")

    assert resp.status == 200
