from flask import Blueprint
from timefliptt.views import RenderTemplateView

blueprint = Blueprint('visitor', __name__)


class GraphsView(RenderTemplateView):
    template_name = 'graphs.html'


blueprint.add_url_rule('/', view_func=GraphsView.as_view('graphs'))


class TasksView(RenderTemplateView):
    template_name = 'tasks.html'


blueprint.add_url_rule('/tasks', view_func=TasksView.as_view('tasks'))


class History(RenderTemplateView):
    template_name = 'history.html'


blueprint.add_url_rule('/history', view_func=History.as_view('history'))


class ReportsView(RenderTemplateView):
    template_name = 'reports.html'


blueprint.add_url_rule('/reports', view_func=ReportsView.as_view('reports'))
