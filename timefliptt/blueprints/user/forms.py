import re

import wtforms.widgets
from flask_wtf import FlaskForm
import wtforms as f
from wtforms.widgets.html5 import ColorInput


HEX_COLOR = re.compile(r'^#[0-9a-fA-F]{6}$')


def is_valid_hex_color(form, field):
    if not HEX_COLOR.match(field.data):
        raise f.ValidationError('This is not a valid color')


class CategoryForm(FlaskForm):
    category_id = f.IntegerField(default=-1, widget=wtforms.widgets.HiddenInput())
    category_name = f.StringField(validators=[f.validators.input_required()])

    submit = f.SubmitField('Submit')


class TaskForm(FlaskForm):
    task_id = f.IntegerField(default=-1, widget=wtforms.widgets.HiddenInput())
    category = f.SelectField('Category', coerce=int)

    task_name = f.StringField(validators=[f.validators.input_required()])
    color = f.StringField(validators=[is_valid_hex_color], widget=ColorInput())

    submit = f.SubmitField('Submit')
