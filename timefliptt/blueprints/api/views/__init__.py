import flask
from flask import Blueprint

from typing import Union

from werkzeug.exceptions import NotFound, Forbidden

blueprint = Blueprint('api', __name__)


# error handling
@blueprint.errorhandler(400)
@blueprint.errorhandler(422)
def handle_error(err):
    headers = err.data.get('headers', None)
    messages = err.data.get('messages', ['Invalid request.'])
    data = {'status': err.code, 'message': 'Error while handling parameters', 'errors': messages}
    if headers:
        return flask.jsonify(data), err.code, headers
    else:
        return flask.jsonify(data), err.code


@blueprint.errorhandler(403)
@blueprint.errorhandler(404)
@blueprint.errorhandler(409)
def handle_error_s(err: Union[NotFound, Forbidden]):
    return flask.jsonify(status=err.code, message=err.description), err.code


from timefliptt.blueprints.api.views import views_timeflip, views_tasks, views_history, views_statistics  # noqa