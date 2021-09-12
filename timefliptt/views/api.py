from flask import Blueprint, Response, jsonify
from flask.views import MethodView
from pytimefliplib.async_client import AsyncClient, TimeFlipRuntimeError

from timefliptt.timeflip import run_coroutine_on_timeflip, CoroutineError

blueprint = Blueprint('api', __name__)


class StatusView(MethodView):
    @staticmethod
    async def get_info(client: AsyncClient) -> dict:
        return {
            'status': 'ok',
            'facet': client.current_facet_value,
            'battery': await client.battery_level(),
            'paused': client.paused,
            'locked': client.locked
        }

    async def get(self) -> Response:
        try:
            return jsonify(**await run_coroutine_on_timeflip(self.get_info, full_setup=True))
        except (CoroutineError, TimeFlipRuntimeError) as e:
            return jsonify(**{
                'status': 'error',
                'msg': e
            })


blueprint.add_url_rule('/api/status', view_func=StatusView.as_view('status'))
