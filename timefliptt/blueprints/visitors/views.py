from flask import Blueprint

from timefliptt.blueprints.base_models import Category, Task
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

        return ctx


blueprint.add_url_rule('/tasks', view_func=TasksView.as_view('tasks'))


# -- History
class History(RenderTemplateView):
    template_name = 'visitors/history.html'


blueprint.add_url_rule('/history', view_func=History.as_view('history'))


class ReportsView(RenderTemplateView):
    template_name = 'visitors/reports.html'


blueprint.add_url_rule('/reports', view_func=ReportsView.as_view('reports'))
