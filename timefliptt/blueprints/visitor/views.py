import flask
from flask import Blueprint, Response, abort
import flask_login
from flask_wtf import FlaskForm
from is_safe_url import is_safe_url

from typing import Union

from pytimefliplib.async_client import TimeFlipRuntimeError

from timefliptt.app import db, timeflip_daemon
from timefliptt.blueprints.base_views import FormView
from timefliptt.blueprints.base_models import User
from timefliptt.blueprints.visitor.forms import LoginForm, AddDeviceForm

blueprint = Blueprint('visitor', __name__)


class LoginView(FormView):
    template_name = 'visitor/login.html'
    form_class = LoginForm

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        ctx['next'] = flask.request.args.get('next', '')
        return ctx

    def dispatch_request(self, *args, **kwargs):
        if flask_login.current_user.is_authenticated:
            url = flask.request.args.get('next', flask.url_for('user.graphs'))
            if is_safe_url(url, {}):
                return flask.redirect(url)
            else:
                abort(400)

        return super().dispatch_request(*args, **kwargs)

    def get_form(self) -> FlaskForm:
        form = super().get_form()
        form.address.choices = [
            (u.device_address, '{} ({})'.format(u.device_address, u.name)) for u in User.query.all()
        ]

        return form

    def form_valid(self, form: LoginForm) -> Union[str, Response]:

        user = User.query.filter(User.device_address.is_(form.address.data)).all()

        if len(user) != 1 or not user[0].is_correct_password(form.password.data):
            flask.flash('Incorrect user or password.', 'error')
            return self.form_invalid(form)

        flask_login.login_user(user[0])

        if flask.current_app.config.get('WITH_TIMEFLIP', False):
            try:
                timeflip_daemon.connect_and_setup(form.address.data, form.password.data)
            except TimeFlipRuntimeError as e:
                flask.flash(
                    'Error while trying to reach device (some function may not be available): {}'.format(e), 'error')

        self.success_url = flask.url_for('user.graphs')
        if form.next.data:
            if is_safe_url(form.next.data, {}):
                self.success_url = form.next.data
            else:
                abort(400)

        return super().form_valid(form)


blueprint.add_url_rule('/', view_func=LoginView.as_view('login'))


@flask_login.login_required
@blueprint.route('/logout', endpoint='logout')
def logout():
    flask_login.logout_user()

    if flask.current_app.config.get('WITH_TIMEFLIP', False):
        timeflip_daemon.logout()

    flask.flash('You are now disconnected.')
    return flask.redirect(flask.url_for('visitor.login'))


class AddDeviceView(FormView):
    template_name = 'visitor/add_device.html'
    form_class = AddDeviceForm

    def form_valid(self, form: AddDeviceForm) -> Union[str, Response]:
        if form.password.data != form.password_repeat.data:
            form.password_repeat.errors.append('The two passwords must be the same')
            return self.form_invalid(form)

        user = User.create(form.name.data, form.address.data, form.password.data)
        db.session.add(user)
        db.session.commit()

        flask.flash('Added new user {}.'.format(user.name))

        self.success_url = flask.url_for('visitor.login')
        return super().form_valid(form)


blueprint.add_url_rule('/add-device', view_func=AddDeviceView.as_view('add-device'))
