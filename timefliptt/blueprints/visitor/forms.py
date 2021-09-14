import re

from flask_wtf import FlaskForm
import wtforms as f

MAC_ADDRESS = re.compile(r'^[0-9a-fA-F]{2}(:([0-9a-fA-F]{2})){5}$')


def is_valid_mac(form, field):
    if not MAC_ADDRESS.match(field.data):
        raise f.ValidationError('This is not a valid MAC address')


class LoginForm(FlaskForm):
    address = f.SelectField('Address', validators=[f.validators.InputRequired(), is_valid_mac])
    password = f.PasswordField('Password', validators=[f.validators.InputRequired(), f.validators.Length(6)])
    next = f.HiddenField(default='')

    login_button = f.SubmitField('Login')


class AddDeviceForm(FlaskForm):
    name = f.StringField('Name', validators=[f.validators.InputRequired()])
    address = f.StringField('Address', validators=[f.validators.InputRequired(), is_valid_mac])
    password = f.PasswordField('Password', validators=[f.validators.InputRequired(), f.validators.Length(6)])
    password_repeat = f.PasswordField(
        'Repeat password', validators=[f.validators.InputRequired(), f.validators.Length(6)])

    submit = f.SubmitField('Add')
