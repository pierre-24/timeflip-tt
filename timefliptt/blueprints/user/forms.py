import re

from flask_wtf import FlaskForm
import wtforms as f
from wtforms.widgets.html5 import ColorInput


HEX_COLOR = re.compile(r'^#[0-9a-fA-F]{6}$')


def is_valid_hex_color(form, field):
    if not HEX_COLOR.match(field.data):
        raise f.ValidationError('This is not a valid color')


class TaskForm(FlaskForm):
    task_id = f.HiddenField()

    category_id = f.SelectField('Category', coerce=int, choices=[(-1, 'Create new category')])
    category_name = f.StringField('New category')

    name = f.StringField(validators=[f.validators.input_required()])
    color = f.StringField(validators=[is_valid_hex_color], widget=ColorInput())

    submit = f.SubmitField('Submit')
