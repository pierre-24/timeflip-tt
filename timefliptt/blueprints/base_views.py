from typing import Union, ClassVar

import flask
from flask import current_app, Response
from flask.views import MethodView
from flask_wtf import FlaskForm
from sqlalchemy.exc import SQLAlchemyError

from timefliptt.app import db


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


class FormPostView(MethodView):

    form_class: ClassVar[FlaskForm] = None
    success_url: str = '/'
    failure_url: str = '/'

    form_kwargs: dict = {}
    url_args = []
    url_kwargs = {}

    def get_form_kwargs(self) -> dict:
        return self.form_kwargs

    def get_form(self) -> FlaskForm:
        """Return an instance of the form"""
        return self.form_class(**self.get_form_kwargs())

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
        """If the form is valid, go to success URL"""

        return flask.redirect(self.success_url)

    def form_invalid(self, form: FlaskForm) -> Union[str, Response]:
        """If the form is invalid, go to failure URL with an error"""

        errors = []
        for element in form:
            if len(element.errors) > 0:
                errors.extend(element.errors)

        flask.flash('Error while treating form: {}'.format(', '.join(errors)), 'error')
        return flask.redirect(self.failure_url)


class FormView(RenderTemplateView, FormPostView):

    def get_context_data(self, *args, **kwargs) -> dict:
        """Insert form in context data"""

        context = super().get_context_data(*args, **kwargs)

        if 'form' not in context:
            context['form'] = kwargs.pop('form', self.get_form())

        return context

    def form_invalid(self, form: FlaskForm) -> Union[str, Response]:
        """If the form is invalid, go back to the same page with an error"""

        if current_app.config['DEBUG']:
            print('form is invalid ::')
            for i in form:
                if len(i.errors) != 0:
                    print('-', i, '→', i.errors, '(value is=', i.data, ')')

        return self.get(form=form, *self.url_args, **self.url_kwargs)


class DeleteView(MethodView):

    success_url = ''

    def get_object_to_delete(self, *args, **kwargs):
        raise NotImplementedError()

    def post_deletion(self, obj):
        """Performs an action after deletion from database"""
        pass

    def delete(self, *args, **kwargs) -> Union[Response, str]:
        """Handle delete"""

        obj = self.get_object_to_delete(*args, **kwargs)
        if obj is None:
            flask.abort(403)

        db.session.delete(obj)
        db.session.commit()

        self.post_deletion(obj)

        return flask.redirect(self.success_url)

    def post(self, *args, **kwargs):
        return self.delete(*args, **kwargs)


class DeleteObjectView(DeleteView):
    object_class: ClassVar = None
    kwarg_var = 'id'

    def get_object_to_delete(self, *args, **kwargs):
        try:
            return self.object_class.query.get(flask.request.form.get(self.kwarg_var, -1))
        except SQLAlchemyError:
            return None
