import flask
from flask import Blueprint, Response
from flask_login import login_required

from typing import Union

from timefliptt.app import db
from timefliptt.blueprints.base_models import Category, Task
from timefliptt.blueprints.base_views import RenderTemplateView, FormView
from timefliptt.blueprints.user.forms import TaskForm

blueprint = Blueprint('user', __name__)


class LoginRequiredMixin:
    decorators = [login_required]


class GraphsView(LoginRequiredMixin, RenderTemplateView):
    template_name = 'user/graphs.html'


blueprint.add_url_rule('/graphs', view_func=GraphsView.as_view('graphs'))


class TasksView(LoginRequiredMixin, FormView):
    template_name = 'user/tasks.html'
    form_class = TaskForm
    modal_form = True

    def get_context_data(self, *args, **kwargs) -> dict:
        ctx = super().get_context_data(*args, **kwargs)

        tasks = Task.query.order_by(Task.category_id, Task.date_created.desc()).all()

        categories = {}
        tasks_per_category = {}
        for task in tasks:
            if task.category_id not in tasks_per_category:
                categories[task.category_id] = task.category
                tasks_per_category[task.category_id] = []

            tasks_per_category[task.category_id].append(task)

        ctx['tasks_per_category'] = tasks_per_category
        ctx['categories'] = categories

        return ctx

    def get_form(self) -> TaskForm:
        form = super().get_form()
        form.category_id.choices.extend((c.id, c.name) for c in Category.query.all())

        return form

    def form_valid(self, form: TaskForm) -> Union[str, Response]:
        if form.category_id.data < 0:
            if len(form.category_name.data) == 0:
                form.category_name.errors.append("Name shouldn't be empty")
                return self.form_invalid(form)

            category = Category.create(form.category_name.data)
            db.session.add(category)
            db.session.commit()

            category_id = category.id
        else:
            category_id = form.category_id.data

        task = Task.create(form.name.data, category_id, form.color.data)
        db.session.add(task)
        db.session.commit()

        self.success_url = flask.url_for('user.tasks')
        return super().form_valid(form)


blueprint.add_url_rule('/tasks', view_func=TasksView.as_view('tasks'))


class History(LoginRequiredMixin, RenderTemplateView):
    template_name = 'user/history.html'


blueprint.add_url_rule('/history', view_func=History.as_view('history'))


class ReportsView(LoginRequiredMixin, RenderTemplateView):
    template_name = 'user/reports.html'


blueprint.add_url_rule('/reports', view_func=ReportsView.as_view('reports'))
