import re

from marshmallow import ValidationError, validate
from marshmallow_sqlalchemy import SQLAlchemySchemaOpts, SQLAlchemySchema, auto_field
from marshmallow_sqlalchemy.fields import Nested

from webargs.flaskparser import FlaskParser
from marshmallow import EXCLUDE

from timefliptt.app import db
from timefliptt.blueprints.base_models import Category, Task, TimeFlipDevice, FacetToTask, HistoryElement


class Parser(FlaskParser):
    DEFAULT_UNKNOWN_BY_LOCATION = {'query': EXCLUDE}


class BaseOpts(SQLAlchemySchemaOpts):
    def __init__(self, meta, ordered=False):
        if not hasattr(meta, 'sqla_session'):
            meta.sqla_session = db.session
        super(BaseOpts, self).__init__(meta, ordered=ordered)


class BaseSchema(SQLAlchemySchema):
    OPTIONS_CLASS = BaseOpts


HEX_COLOR = re.compile(r'^#[0-9a-fA-F]{6}$')


def validate_color(color: str):
    if not HEX_COLOR.match(color):
        raise ValidationError('This is not a valid color')


class TaskSchema(BaseSchema):
    class Meta:
        model = Task

    id = auto_field(required=True, validate=validate.Range(min=0))
    name = auto_field(required=True, validate=validate.Length(min=1))
    color = auto_field(validate=validate_color, required=True)
    category = auto_field('category_id', required=True, validate=validate.Range(min=0))


class CategorySchema(BaseSchema):
    class Meta:
        model = Category

    id = auto_field(required=True, validate=validate.Range(min=0))
    name = auto_field(required=True, validate=validate.Length(min=1))
    tasks = Nested(TaskSchema, many=True, exclude=('category', ))


MAC_ADDRESS = re.compile(r'^[0-9a-fA-F]{2}(:([0-9a-fA-F]{2})){5}$')


def validate_mac(address: str):
    if not MAC_ADDRESS.match(address):
        raise ValidationError('This is not a valid MAC address')


class TimeFlipDeviceSchema(BaseSchema):
    class Meta:
        model = TimeFlipDevice

    id = auto_field(required=True, validate=validate.Range(min=0))
    address = auto_field(required=True, validate=validate_mac)
    password = auto_field(required=True, validate=validate.Length(equal=6))

    name = auto_field(validate=validate.Length(min=1, max=19))
    calibration = auto_field()


class FacetToTaskSchema(BaseSchema):
    class Meta:
        model = FacetToTask

    id = auto_field(required=True, validate=validate.Range(min=0))
    facet = auto_field(required=True, validate=validate.Range(min=0, max=62))
    task = Nested(TaskSchema)
    timeflip_device = Nested(TimeFlipDeviceSchema)


class HistoryElementSchema(BaseSchema):
    class Meta:
        model = HistoryElement

    id = auto_field(required=True, validate=validate.Range(min=0))
    start = auto_field(required=True)
    end = auto_field(required=True)
    original_facet = auto_field(required=True)
    comment = auto_field(required=True)

    task = Nested(TaskSchema)
    timeflip_device = auto_field('timeflip_device_id')
