from flask import Blueprint

blueprint = Blueprint('api', __name__)

from timefliptt.blueprints.api.views import views_timeflip  # noqa