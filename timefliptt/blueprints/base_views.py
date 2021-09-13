from typing import Union, ClassVar

import flask
from flask import current_app, Response
from flask.views import MethodView
from flask_wtf import FlaskForm


class ContextDataMixin:
    """Defines the context data mixin, with some extra information
    """

    def get_context_data(self, *args, **kwargs) -> dict:
        context = {}
        context.update(**current_app.config['APP_INFO'])

        return context


class RenderTemplateView(MethodView, ContextDataMixin):
    """Base GET view with template rendering"""

    template_name = None

    def get(self, *args, **kwargs) -> Union[str, Response]:
        """Handle GET: render template
        """

        if not self.template_name:
            raise ValueError('template_name')

        context_data = self.get_context_data(*args, **kwargs)
        return flask.render_template(self.template_name, **context_data)


class FormView(RenderTemplateView):

    form_class: ClassVar[FlaskForm] = None
    success_url: str = '/'
    failure_url: str = '/'
    modal_form = False

    form_kwargs = {}

    def get_form_kwargs(self) -> dict:
        return self.form_kwargs

    def get_form(self) -> FlaskForm:
        """Return an instance of the form"""
        return self.form_class(**self.get_form_kwargs())

    def get_context_data(self, *args, **kwargs) -> dict:
        """Insert form in context data"""

        context = super().get_context_data(*args, **kwargs)

        if 'form' not in context:
            context['form'] = kwargs.pop('form', self.get_form())

        return context

    def post(self, *args, **kwargs) -> Union[str, Response]:
        """Handle POST: validate form."""

        self.url_args = args
        self.url_kwargs = kwargs
        if not self.form_class:
            raise ValueError('form_class')

        form = self.get_form()

        if form.validate_on_submit():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form: FlaskForm) -> Union[str, Response]:
        """If the form is valid, go to the success url"""
        return flask.redirect(self.success_url)

    def form_invalid(self, form: FlaskForm) -> Union[str, Response]:
        """If the form is invalid, go back to the same page with an error"""

        if current_app.config['DEBUG']:
            print('form is invalid ::')
            for i in form:
                if len(i.errors) != 0:
                    print('-', i, '→', i.errors, '(value is=', i.data, ')')

        if not self.modal_form:
            return self.get(form=form, *self.url_args, **self.url_kwargs)
        else:
            return flask.redirect(self.failure_url)