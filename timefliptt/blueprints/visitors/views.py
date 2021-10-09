from flask import Blueprint

from timefliptt.blueprints.base_views import RenderTemplateView

blueprint = Blueprint('visitors', __name__)


# --- Graphs
class GraphsView(RenderTemplateView):
    template_name = 'visitors/graphs.html'


blueprint.add_url_rule('/graphs', view_func=GraphsView.as_view('graphs'))


# --- Timeflip
class TimeflipView(RenderTemplateView):
    template_name = 'visitors/timeflip.html'


blueprint.add_url_rule('/timeflip', view_func=TimeflipView.as_view('timeflip'))


# --- Tasks
class TasksView(RenderTemplateView):
    template_name = 'visitors/tasks.html'


blueprint.add_url_rule('/tasks', view_func=TasksView.as_view('tasks'))


# -- History
class History(RenderTemplateView):
    template_name = 'visitors/history.html'


blueprint.add_url_rule('/history', view_func=History.as_view('history'))


class ReportsView(RenderTemplateView):
    template_name = 'visitors/reports.html'


blueprint.add_url_rule('/reports', view_func=ReportsView.as_view('reports'))
