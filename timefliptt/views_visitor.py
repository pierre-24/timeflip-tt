from flask import Blueprint, Response, make_response
from flask.views import MethodView

blueprint = Blueprint('visitor', __name__)


class Index(MethodView):
    def get(self) -> Response:
        return make_response('whatever', 200)


blueprint.add_url_rule('/', view_func=Index.as_view('index'))


