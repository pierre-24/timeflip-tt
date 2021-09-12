import flask
from flask import current_app
from flask.views import MethodView


class ContextDataMixin:
    """Defines the context data mixin, with some extra information
    """

    def get_context_data(self, *args, **kwargs):
        context = {}
        context.update(**current_app.config['APP_INFO'])

        return context


class RenderTemplateView(MethodView, ContextDataMixin):
    """Base GET view with template rendering"""

    template_name = None

    def get(self, *args, **kwargs):
        """Handle GET: render template
        """

        if not self.template_name:
            raise ValueError('template_name')

        context_data = self.get_context_data(*args, **kwargs)
        return flask.render_template(self.template_name, **context_data)
