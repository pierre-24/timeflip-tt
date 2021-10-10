import asyncio.exceptions
from threading import Lock, Thread
from bleak import BleakError

from typing import Callable, Coroutine, Any

from pytimefliplib.async_client import AsyncClient, TimeFlipRuntimeError, NotConnectedError


class CoroutineError(Exception):
    pass


_client: AsyncClient = None
_loop: asyncio.AbstractEventLoop = None
_thread: Thread = None
_lock = Lock()

_timeflip_address = ''
_timeflip_password = ''


class DaemonStopped(Exception):
    def __init__(self):
        super().__init__('Daemon is currently stopped!')


def daemon_start():
    """Setup and start daemon
    """

    global _loop, _thread

    def _start_loop(loop):
        asyncio.set_event_loop(loop)
        loop.run_forever()

    _loop = asyncio.new_event_loop()
    _thread = Thread(target=_start_loop, args=(_loop,), daemon=True)
    _thread.start()


def daemon_stop():
    global _thread, _loop, _lock

    hard_logout()

    with _lock:
        if _loop is not None:
            _loop.call_soon_threadsafe(_loop.stop)
            _thread.join()
            _loop = None
            _thread = None


def daemon_status():
    global _loop, _lock, _timeflip_address

    with _lock:
        if _loop is None:
            return {'daemon_status': 'stopped'}
        elif _timeflip_address == '':
            return {'daemon_status': 'disconnected'}
        else:
            return {'daemon_status': 'connected', 'address': _timeflip_address}


def soft_connect(address: str, password: str):
    """Setup everything so that it will connect at next request
    """

    global _lock, _timeflip_address, _timeflip_password, _loop

    with _lock:
        if _loop is None:
            raise DaemonStopped()

        _timeflip_address = address
        _timeflip_password = password


def hard_connect(address: str, password: str) -> bool:
    """Force a connexion
    """

    global _lock, _client, _loop

    soft_connect(address, password)
    return _connect()


def _connect() -> bool:

    global _lock, _loop, _client, _timeflip_address, _timeflip_password

    async def _connect_and_setup(client: AsyncClient, passwd: str):
        await client.connect()
        await client.setup(password=passwd)

    with _lock:
        if _loop is None:
            raise DaemonStopped()

        if _timeflip_address != '' and _timeflip_password != '':
            _client = AsyncClient(_timeflip_address)
            _run_coro(_connect_and_setup, passwd=_timeflip_password)
            return True

    return False


def connected_to(address: str) -> bool:
    global _lock, _loop, _timeflip_address

    with _lock:
        if _loop is None:
            raise DaemonStopped()

        return address == _timeflip_address


def try_reconnect() -> bool:
    """Attempt reconnect, if allowed"""

    return _connect()


def hard_logout():
    """Force logout
    """

    global _lock, _client, _loop, _timeflip_address, _timeflip_password

    async def _disconnect(client: AsyncClient):
        try:
            await client.disconnect()
        except NotConnectedError:
            pass  # oh ... well ;)

    with _lock:
        if _loop is None:
            raise DaemonStopped()

        _timeflip_address = ''
        _timeflip_password = ''

        if _client is not None:
            _run_coro(_disconnect)
            _client = None


def _run_coro(coro: Callable[[AsyncClient, Any], Coroutine], **kwargs) -> Any:
    """Actually run the corountine (without any check!!)
    """

    global _client, _loop

    try:
        task = asyncio.run_coroutine_threadsafe(coro(_client, **kwargs), _loop)
        return task.result()
    except asyncio.exceptions.TimeoutError as e:
        raise TimeFlipRuntimeError(e)


def run_coro(coro: Callable[[AsyncClient, Any], Coroutine], retry: int = 1, **kwargs) -> Any:
    global _lock, _loop, _client, _timeflip_address

    attempts = retry + 1

    for attempt in range(attempts):
        try:
            with _lock:
                if _loop is None:
                    raise DaemonStopped()

                if _client is None:
                    raise NotConnectedError()

                return _run_coro(coro, **kwargs)
        except (NotConnectedError, BleakError) as e:
            if attempt < retry:
                try_reconnect()
            else:
                if type(e) is BleakError:
                    raise TimeFlipRuntimeError(e)
                else:
                    raise e
