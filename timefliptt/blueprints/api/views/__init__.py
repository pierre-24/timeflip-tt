from flask import Blueprint

blueprint = Blueprint('api', __name__)

from timefliptt.blueprints.api.views import views_timeflip, views_tasks, views_history  # noqa