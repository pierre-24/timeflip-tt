import asyncio

from typing import List

from webargs import fields, validate
from marshmallow import Schema, post_load

import flask
from flask import Response, jsonify
from flask.views import MethodView

from pytimefliplib.async_client import AsyncClient, TimeFlipRuntimeError, CHARACTERISTICS
from bleak import BleakScanner, BleakClient, BleakError
from asyncio import TimeoutError

from timefliptt.app import db
from timefliptt.blueprints.api.views import blueprint
from timefliptt.timeflip import run_coro, connected_to, hard_connect, hard_logout, soft_connect
from timefliptt.blueprints.base_models import TimeFlipDevice, FacetToTask, Task
from timefliptt.blueprints.api.schemas import TimeFlipDeviceSchema, Parser, FacetToTaskSchema


parser = Parser()


class AvailableDevicesView(MethodView):
    """List the available TimeFlip devices

    Inspired by
    https://github.com/pierre-24/pytimefliplib/blob/b4ceda/pytimefliplib/scripts/discover.py#L11
    """
    async def get_devices(self) -> List[dict]:
        avail_timeflip = []
        other_devices = []

        devices = await BleakScanner.discover()
        for d in devices:
            try:
                async with BleakClient(d) as client:
                    _ = await client.read_gatt_char(CHARACTERISTICS['facet'])
                    avail_timeflip.append(d)
            except (BleakError, TimeoutError):
                other_devices.append(d)

        users: List[TimeFlipDevice] = TimeFlipDevice.query.all()

        def get_id(address: str):
            pk = -1
            for u in users:
                if u.address == address:
                    return u.id
            return pk

        return [{
            'address': d.address,
            'name': d.name,
            'id': get_id(d.address)
        } for d in avail_timeflip]

    def get(self) -> Response:
        loop = asyncio.new_event_loop()
        t = loop.create_task(self.get_devices())
        available_devices = loop.run_until_complete(t)
        loop.close()
        return jsonify(discovered=available_devices)


blueprint.add_url_rule('/api/devices/', view_func=AvailableDevicesView.as_view('devices'))


class TimeFlipsView(MethodView):
    def get(self) -> Response:
        """List registered devices
        """
        return jsonify(timeflip_devices=TimeFlipDeviceSchema(many=True).dump(TimeFlipDevice.query.all()))

    @parser.use_kwargs(TimeFlipDeviceSchema(exclude=('id', )), location='json')
    def post(self, name: str, address: str, password: str) -> Response:
        """Register a new device
        """

        device = TimeFlipDevice.create(name, address, password)

        db.session.add(device)
        db.session.commit()

        return TimeFlipDeviceSchema().dump(device)

    def delete(self) -> Response:
        """Disconnect from any device
        """

        hard_logout()
        return jsonify(status='ok')


blueprint.add_url_rule('/api/timeflips/', view_func=TimeFlipsView.as_view('timeflips'))


class TimeFlipView(MethodView):

    class TimeFlipDeviceSimpleSchema(Schema):
        id = fields.Integer(required=True, validate=validate.Range(min=0))

        @post_load
        def make_object(self, data, **kwargs):
            return TimeFlipDevice.query.get(data['id'])

    @parser.use_args(TimeFlipDeviceSimpleSchema, location='view_args')
    def get(self, device: TimeFlipDevice, id: int) -> Response:
        """View information for an existing timeflip
        """

        if device is not None:
            return jsonify(TimeFlipDeviceSchema().dump(device))
        else:
            flask.abort(404)

    @parser.use_args(TimeFlipDeviceSimpleSchema, location='view_args')
    def delete(self, device: TimeFlipDevice, id: int) -> Response:
        """Delete timeflip
        """

        if device is not None:
            db.session.delete(device)
            db.session.commit()
            return jsonify(status='ok')
        else:
            flask.abort(404)


blueprint.add_url_rule('/api/timeflips/<int:id>/', view_func=TimeFlipView.as_view('timeflip'))


class TimeFlipHandleView(MethodView):
    """Route that gather everything that requires communication with the TimeFlip
    """

    @staticmethod
    async def get_info(client: AsyncClient) -> dict:
        return {
            'status': 'ok',
            'address': client.address,
            'name': await client.device_name(),
            'facet': client.current_facet_value,
            'battery': await client.battery_level(),
            'paused': client.paused,
            'locked': client.locked
        }

    @parser.use_args(TimeFlipView.TimeFlipDeviceSimpleSchema, location='view_args')
    def get(self, device: TimeFlipDevice, id: int) -> Response:
        """Get status
        """

        if device is not None:
            if not connected_to(device.address):
                flask.abort(403)

            try:
                data = run_coro(self.get_info)
                return jsonify(data)
            except (TimeFlipRuntimeError, BleakError) as e:
                return jsonify(status='ko', error=str(e))
        else:
            flask.abort(404)

    @parser.use_args(TimeFlipView.TimeFlipDeviceSimpleSchema, location='view_args')
    def post(self, device: TimeFlipDevice, id: int) -> Response:
        """Connect to the device"""

        if device is not None:
            try:
                hard_connect(device.address, device.password)
                return jsonify(status='ok')
            except (TimeFlipRuntimeError, BleakError) as e:
                return jsonify(status='ko', error=str(e))
        else:
            flask.abort(404)

    @staticmethod
    async def set_new_password(client: AsyncClient, password: str):
        await client.set_password(password)

    @staticmethod
    async def set_new_name(client: AsyncClient, name: str):
        await client.set_name(name)

    @parser.use_args(TimeFlipView.TimeFlipDeviceSimpleSchema, location='view_args')
    @parser.use_kwargs(
        {'name': fields.Str(), 'password': fields.Str(validate=validate.Length(equal=6))}, location='json')
    def put(self, device: TimeFlipDevice, **kwargs) -> Response:
        """Modify device
        """

        if device is not None:
            if not connected_to(device.address):
                flask.abort(403)

            try:
                if 'name' in kwargs:
                    device.name = kwargs['name']
                    run_coro(self.set_new_name, name=device.name)

                if 'password' in kwargs:
                    device.password = kwargs['password']
                    run_coro(self.set_new_password, password=device.password)
                    soft_connect(device.address, kwargs['password'])
            except (BleakError, TimeFlipRuntimeError) as e:
                return jsonify(status='ko', error=str(e))

            db.session.add(device)
            db.session.commit()

            return jsonify(status='ok')
        else:
            flask.abort(404)


blueprint.add_url_rule('/api/timeflips/<int:id>/handle', view_func=TimeFlipHandleView.as_view('timeflip-handle'))


class FacetsView(MethodView):

    @parser.use_args(TimeFlipView.TimeFlipDeviceSimpleSchema, location='view_args')
    def get(self, device: TimeFlipDevice, id: int) -> Response:
        """Get facets
        """

        if device is not None:
            return jsonify(
                facet_to_task=FacetToTaskSchema(many=True, exclude=('timeflip_device', 'id')).dump(
                    FacetToTask.query.filter(FacetToTask.timeflip_device_id.is_(device.id)).all()
                ))
        else:
            flask.abort(404)


blueprint.add_url_rule('/api/timeflips/<int:id>/facets/', view_func=FacetsView.as_view('timeflip-facets'))


class FacetView(MethodView):

    class DeviceAndFacetSchema(Schema):
        id = fields.Integer(required=True, validate=validate.Range(min=0))
        facet = fields.Integer(required=True, validate=validate.Range(min=0, max=62))

        @post_load
        def make_object(self, data, **kwargs):
            return {
                'device': TimeFlipDevice.query.get(data['id']),
                'facet': data['facet']
            }

    class SimpleFacetToTaskSchema(Schema):
        id = fields.Integer(required=True, validate=validate.Range(min=0))
        facet = fields.Integer(required=True, validate=validate.Range(min=0, max=62))

        @post_load
        def make_object(self, data, **kwargs):
            return {
                'ftt': FacetToTask.query
                .filter(FacetToTask.timeflip_device_id.is_(data['id']))
                .filter(FacetToTask.facet.is_(data['facet']))
                .first()
            }

    class TaskSimpleSchema(Schema):
        task = fields.Integer(required=True, validate=validate.Range(min=0))

        @post_load
        def make_object(self, data, **kwargs):
            return {
                'task': Task.query.get(data['task'])
            }

    @parser.use_kwargs(SimpleFacetToTaskSchema, location='view_args')
    def get(self, id: int, facet: int, ftt: FacetToTask):
        """View which task is associated to this facet
        """

        if ftt is not None:
            return jsonify(FacetToTaskSchema(exclude=('id', 'timeflip_device')).dump(ftt))
        else:
            flask.abort(404)

    @parser.use_kwargs(DeviceAndFacetSchema, location='view_args')
    @parser.use_kwargs(TaskSimpleSchema, location='json')
    def put(self, id: int, facet: int, device: TimeFlipDevice, task: Task) -> Response:
        """Add a Task to a facet
        """

        if device is not None and task is not None:
            ftt = FacetToTask.query\
                .filter(FacetToTask.timeflip_device_id.is_(device.id))\
                .filter(FacetToTask.facet.is_(facet))\
                .first()

            if ftt is not None:
                ftt.task_id = task.id
            else:
                ftt = FacetToTask.create(device, facet, task)

            db.session.add(ftt)
            db.session.commit()

            return jsonify(FacetToTaskSchema(exclude=('timeflip_device', 'id')).dump(ftt))
        else:
            flask.abort(404)

    @parser.use_kwargs(SimpleFacetToTaskSchema, location='view_args')
    def delete(self, id: int, facet: int, ftt: FacetToTask):
        """Remove the task from the facet (if it exists)
        """

        if ftt is not None:
            db.session.delete(ftt)
            db.session.commit()

            return jsonify(status='ok')
        else:
            flask.abort(404)


blueprint.add_url_rule('/api/timeflips/<int:id>/facets/<int:facet>/', view_func=FacetView.as_view('timeflip-facet'))
