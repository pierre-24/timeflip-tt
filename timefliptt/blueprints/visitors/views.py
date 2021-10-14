import flask
from flask import Blueprint

from timefliptt.timeflip import hard_logout
from timefliptt.blueprints.base_models import TimeFlipDevice
from timefliptt.blueprints.base_views import RenderTemplateView

blueprint = Blueprint('visitors', __name__)


# --- Graphs
class GraphsView(RenderTemplateView):
    template_name = 'visitors/graphs.html'


blueprint.add_url_rule('/', view_func=GraphsView.as_view('graphs'))


# --- Timeflip
class TimeflipView(RenderTemplateView):
    template_name = 'visitors/timeflip.html'

    def get_context_data(self, *args, **kwargs) -> dict:

        device = TimeFlipDevice.query.get(kwargs.get('id', -1))
        if device is None:
            flask.abort(404)

        ctx = super().get_context_data(*args, **kwargs)
        ctx['timeflip_device'] = device
        return ctx


blueprint.add_url_rule('/timeflip-<int:id>', view_func=TimeflipView.as_view('timeflip'))


class TimeflipAddView(RenderTemplateView):
    template_name = 'visitors/timeflip-add.html'

    def get(self, *args, **kwargs):
        hard_logout()  # otherwise, this messed up the search for new devices
        return super().get(*args, **kwargs)


blueprint.add_url_rule('/timeflip-add', view_func=TimeflipAddView.as_view('timeflip-add'))


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
