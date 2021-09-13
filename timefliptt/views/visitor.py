from flask import Blueprint
from timefliptt.views import RenderTemplateView

blueprint = Blueprint('visitor', __name__)


class LoginView(RenderTemplateView):
    template_name = 'login.html'


blueprint.add_url_rule('/', view_func=LoginView.as_view('login'))
