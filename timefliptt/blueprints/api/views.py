from flask import Blueprint, Response, jsonify
from flask.views import MethodView
from pytimefliplib.async_client import AsyncClient, TimeFlipRuntimeError

from bleak import BleakScanner, BleakClient, BleakError
from asyncio import TimeoutError
from pytimefliplib.async_client import CHARACTERISTICS

from timefliptt.timeflip import run_coro
from timefliptt.blueprints.base_models import User
from timefliptt.blueprints.base_views import LoginRequiredMixin

blueprint = Blueprint('api', __name__)


class ListAvailableDevices(MethodView):
    """List the available TimeFlip devices

    Inspired by
    https://github.com/pierre-24/pytimefliplib/blob/b4ceda/pytimefliplib/scripts/discover.py#L11
    """
    async def get(self) -> Response:
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
            {'address': d.address, 'name': d.name, 'pairable': d.address not in user_addresses} for d in avail_timeflip
        ])


blueprint.add_url_rule('/api/discover', view_func=ListAvailableDevices.as_view('discover'))


class StatusView(LoginRequiredMixin, MethodView):
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

    async def get(self) -> Response:
        try:
            return jsonify(**run_coro(self.get_info))
        except TimeFlipRuntimeError as e:
            return jsonify(**{
                'status': 'error',
                'msg': str(e)
            })


blueprint.add_url_rule('/api/status', view_func=StatusView.as_view('status'))
