import asyncio.exceptions
from typing import Callable, Coroutine, Any

from bleak import BleakError

from flask import current_app
from pytimefliplib.async_client import AsyncClient, TimeFlipRuntimeError


class CoroutineError(Exception):
    pass


async def run_coroutine_on_timeflip(coro: Callable[[AsyncClient], Coroutine], full_setup: bool = False) -> Any:
    """Run a coroutine on a connected TimeFlip

    :param full_setup: use `client.setup()` (to access lock state and facet) instead of `client.login()`
    :param coro: the coroutine
    """
    config = current_app.config['TIMEFLIP']

    try:
        async with AsyncClient(config['address']) as client:
            if full_setup:
                await client.setup(password=config['password'])
            else:
                await client.login(password=config['password'])
            result = await coro(client)
    except asyncio.exceptions.TimeoutError as e:
        raise CoroutineError(e)
    except BleakError as e:
        raise TimeFlipRuntimeError(e)

    return result
