import flask
from flask import Blueprint, Response

from typing import Union

import flask_login

from pytimefliplib.async_client import AsyncClient

from timefliptt.app import db
from timefliptt.timeflip import run_coro, soft_connect
from timefliptt.blueprints.base_models import Category, Task, User
from timefliptt.blueprints.base_views import RenderTemplateView, FormPostView, LoginRequiredMixin
from timefliptt.blueprints.user.forms import TaskForm, CategoryForm, ModifyDevicePasswordForm, ModifyDeviceNameForm

blueprint = Blueprint('user', __name__)


# --- Graphs
class GraphsView(RenderTemplateView):
    template_name = 'user/graphs.html'


blueprint.add_url_rule('/graphs', view_func=GraphsView.as_view('graphs'))


# --- Timeflip
class TimeflipView(LoginRequiredMixin, RenderTemplateView):
    template_name = 'user/timeflip.html'

    def get_context_data(self, *args, **kwargs) -> dict:
        ctx = super().get_context_data(*args, **kwargs)

        ctx['form_modify_passwd'] = ModifyDevicePasswordForm()
        ctx['form_modify_name'] = ModifyDeviceNameForm()
        ctx['form_modify_name'].name.data = flask_login.current_user.name

        return ctx


blueprint.add_url_rule('/timeflip', view_func=TimeflipView.as_view('timeflip'))


class ModifyDevicePasswordView(LoginRequiredMixin, FormPostView):
    form_class = ModifyDevicePasswordForm

    @staticmethod
    async def set_new_password(client: AsyncClient, password: str):
        await client.set_password(password)

    def form_valid(self, form: ModifyDevicePasswordForm) -> Union[str, Response]:

        self.success_url = self.failure_url = flask.url_for('user.timeflip')

        if not flask_login.current_user.is_correct_password(form.old_password.data):
            form.old_password.errors.append('Incorrect old password')
            return self.form_invalid(form)

        if form.password.data != form.repeat_password.data:
            form.repeat_password.errors.append('The two passwords does not match')
            return self.form_invalid(form)

        # change in timeflip
        run_coro(self.set_new_password, password=form.password.data)

        # change in db
        user = flask_login.current_user
        user.password_hash = User.hash_pass(form.password.data)
        db.session.add(user)
        db.session.commit()

        # change in session
        flask.session['password'] = form.password.data
        soft_connect(user.device_address, form.password.data)

        flask.flash('TimeFlip password changed!')
        return super().form_valid(form)


blueprint.add_url_rule('/timeflip/modify-passwd', view_func=ModifyDevicePasswordView.as_view('timeflip-modify-pass'))


class ModifyDeviceNameView(LoginRequiredMixin, FormPostView):
    form_class = ModifyDeviceNameForm

    @staticmethod
    async def set_new_name(client: AsyncClient, name: str):
        await client.set_name(name)

    def form_valid(self, form: ModifyDeviceNameForm) -> Union[str, Response]:
        self.success_url = self.failure_url = flask.url_for('user.timeflip')

        # change in TimeFlip
        run_coro(self.set_new_name, name=form.name.data)

        # change in db
        user = flask_login.current_user
        user.name = form.name.data
        db.session.add(user)
        db.session.commit()

        flask.flash('TimeFlip name changed!')
        return super().form_valid(form)


blueprint.add_url_rule('/timeflip/modify-name', view_func=ModifyDeviceNameView.as_view('timeflip-modify-name'))


# --- Tasks
class TasksView(RenderTemplateView):
    template_name = 'user/tasks.html'

    def get_context_data(self, *args, **kwargs) -> dict:
        ctx = super().get_context_data(*args, **kwargs)

        # list of task and categories
        categories = dict((c.id, c) for c in Category.query.all())
        tasks = Task.query.order_by(Task.id.desc()).all()

        tasks_per_category = {}
        for task in tasks:
            if task.category_id not in tasks_per_category:
                tasks_per_category[task.category_id] = []

            tasks_per_category[task.category_id].append(task)

        ctx['tasks_per_category'] = tasks_per_category
        ctx['categories'] = categories

        # form
        ctx['form_task'] = TaskForm()
        ctx['form_task'].category.choices = list((k, v.name) for k, v in categories.items())

        ctx['form_category'] = CategoryForm()

        return ctx


blueprint.add_url_rule('/tasks', view_func=TasksView.as_view('tasks'))


# -- History
class History(RenderTemplateView):
    template_name = 'user/history.html'


blueprint.add_url_rule('/history', view_func=History.as_view('history'))


class ReportsView(RenderTemplateView):
    template_name = 'user/reports.html'


blueprint.add_url_rule('/reports', view_func=ReportsView.as_view('reports'))
