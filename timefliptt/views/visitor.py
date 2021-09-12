from flask import Blueprint
from timefliptt.views import RenderTemplateView

blueprint = Blueprint('visitor', __name__)


class Index(RenderTemplateView):
    template_name = 'index.html'


blueprint.add_url_rule('/', view_func=Index.as_view('index'))
