from flask import Blueprint
from flask_login import login_required

from timefliptt.blueprints.base_views import RenderTemplateView

blueprint = Blueprint('user', __name__)


class LoginRequiredMixin:
    decorators = [login_required]


class GraphsView(LoginRequiredMixin, RenderTemplateView):
    template_name = 'user/graphs.html'


blueprint.add_url_rule('/graphs', view_func=GraphsView.as_view('graphs'))


class TasksView(LoginRequiredMixin, RenderTemplateView):
    template_name = 'user/tasks.html'


blueprint.add_url_rule('/tasks', view_func=TasksView.as_view('tasks'))


class History(LoginRequiredMixin, RenderTemplateView):
    template_name = 'user/history.html'


blueprint.add_url_rule('/history', view_func=History.as_view('history'))


class ReportsView(LoginRequiredMixin, RenderTemplateView):
    template_name = 'user/reports.html'


blueprint.add_url_rule('/reports', view_func=ReportsView.as_view('reports'))
