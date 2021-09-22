import asyncio

from flask import Response, jsonify
from flask_restful import Resource
from pytimefliplib.async_client import AsyncClient, TimeFlipRuntimeError

from bleak import BleakScanner, BleakClient, BleakError
from asyncio import TimeoutError
from pytimefliplib.async_client import CHARACTERISTICS

from timefliptt.blueprints.api.views import blueprint
from timefliptt.timeflip import run_coro
from timefliptt.blueprints.base_models import User
from timefliptt.blueprints.base_views import LoginRequiredMixin


class ListAvailableDevices(Resource):
    """List the available TimeFlip devices

    Inspired by
    https://github.com/pierre-24/pytimefliplib/blob/b4ceda/pytimefliplib/scripts/discover.py#L11
    """
    async def get_devices(self) -> Response:
        avail_timeflip = []

        devices = await BleakScanner.discover()
        for d in devices:
            try:
                async with BleakClient(d) as client:
                    _ = await client.read_gatt_char(CHARACTERISTICS['facet'])
                    avail_timeflip.append(d)
            except (BleakError, TimeoutError):
                pass

        user_addresses = [u.device_address for u in User.query.all()]

        return jsonify(discovered=[
            {
                'address': d.address,
                'name': d.name,
                'already_paired': d.address in user_addresses
            } for d in avail_timeflip
        ])

    def get(self):
        loop = asyncio.new_event_loop()
        loop.run_forever()
        return asyncio.run_coroutine_threadsafe(self.get_devices(), loop).result()


blueprint.add_url_rule('/api/timeflip/discover', view_func=ListAvailableDevices.as_view('timeflip-discover'))


class StatusView(LoginRequiredMixin, Resource):
    @staticmethod
    async def get_info(client: AsyncClient) -> dict:
        return {
            'status': 'ok',
            'name': await client.device_name(),
            'facet': client.current_facet_value,
            'battery': await client.battery_level(),
            'paused': client.paused,
            'locked': client.locked
        }

    def get(self) -> Response:
        try:
            return jsonify(**run_coro(self.get_info))
        except TimeFlipRuntimeError as e:
            return jsonify(**{
                'status': 'error',
                'msg': str(e)
            })


blueprint.add_url_rule('/api/timeflip/status', view_func=StatusView.as_view('timeflip-status'))
