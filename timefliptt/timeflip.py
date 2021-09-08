from typing import Callable, Coroutine, Any

from flask import current_app
from pytimefliplib.async_client import AsyncClient


async def run_coroutine_on_timeflip(coro: Callable[[AsyncClient], Coroutine]) -> Any:
    config = current_app.config['TIMEFLIP']
    async with AsyncClient(config['address']) as client:
        await client.setup(password=config['password'])
        result = await coro(client)

    return result
