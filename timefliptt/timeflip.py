import asyncio.exceptions
from threading import Lock, Thread
from bleak import BleakError

from typing import Callable, Coroutine, Any

from pytimefliplib.async_client import AsyncClient, TimeFlipRuntimeError


class CoroutineError(Exception):
    pass


client: AsyncClient = None
loop: asyncio.AbstractEventLoop = None
thread: Thread = None
lock = Lock()
connected_and_setup = False


class TimeFlipDaemon:
    """Daemon to run things on a connected TimeFlip
    """

    def __init__(self):
        pass

    @staticmethod
    def _start_loop(loop: asyncio.AbstractEventLoop):
        asyncio.set_event_loop(loop)
        loop.run_forever()

    def start(self):
        global loop, thread

        loop = asyncio.new_event_loop()
        thread = Thread(target=TimeFlipDaemon._start_loop, args=(loop, ), daemon=True)
        thread.start()

    def connect_and_setup(self, address: str, password: str):
        global client, lock, connected_and_setup

        with lock:
            client = AsyncClient(address)
            self._run_coro(self._coro_connect_and_setup, password=password)
            connected_and_setup = True

    def logout(self):
        global lock, connected_and_setup

        with lock:
            if connected_and_setup:
                self._run_coro(self._coro_disconnect)
                connected_and_setup = False

    def run_coro(self, coro: Callable[[AsyncClient, ...], Coroutine], **kwargs) -> Any:
        global lock

        with lock:
            return self._run_coro(coro, **kwargs)

    def stop(self):
        global thread, loop, lock

        self.logout()

        with lock:
            loop.call_soon_threadsafe(loop.stop)
            thread.join()

    def _run_coro(self, coro: Callable[[AsyncClient, ...], Coroutine], **kwargs) -> Any:
        global client, loop

        try:
            task = asyncio.run_coroutine_threadsafe(coro(client, **kwargs), loop)
            return task.result()
        except asyncio.exceptions.TimeoutError as e:
            raise TimeFlipRuntimeError(e)
        except BleakError as e:
            raise TimeFlipRuntimeError(e)

    async def _coro_connect_and_setup(self, client: AsyncClient, password: str):
        await client.connect()
        await client.setup(password=password)

    async def _coro_disconnect(self, client: AsyncClient):
        await client.disconnect()
