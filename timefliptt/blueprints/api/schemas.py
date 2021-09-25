import re

from marshmallow import ValidationError
from marshmallow_sqlalchemy import SQLAlchemySchemaOpts, SQLAlchemySchema, auto_field
from marshmallow_sqlalchemy.fields import Nested

from webargs.flaskparser import FlaskParser
from marshmallow import EXCLUDE

from timefliptt.app import db
from timefliptt.blueprints.base_models import Category, Task


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

    id = auto_field()
    name = auto_field()
    color = auto_field(validate=validate_color)
    category = auto_field('category_id')


class CategorySchema(BaseSchema):
    class Meta:
        model = Category

    id = auto_field()
    name = auto_field()
    tasks = Nested(TaskSchema, many=True, exclude=('category', ))
