import asyncio.exceptions
from typing import Callable, Coroutine, Any

from bleak import BleakError

from flask import current_app
from pytimefliplib.async_client import AsyncClient, TimeFlipRuntimeError


class CoroutineError(Exception):
    pass


async def run_coroutine_on_timeflip(coro: Callable[[AsyncClient], Coroutine]) -> Any:
    config = current_app.config['TIMEFLIP']

    try:
        async with AsyncClient(config['address']) as client:
            await client.setup(password=config['password'])
            result = await coro(client)
    except asyncio.exceptions.TimeoutError as e:
        raise CoroutineError(e)
    except BleakError as e:
        raise TimeFlipRuntimeError(e)

    return result
