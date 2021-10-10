import flask
from flask import jsonify, Response
from flask.views import MethodView

from webargs import fields
from marshmallow import Schema, post_load, validate

from timefliptt.app import db
from timefliptt.blueprints.api.views import blueprint
from timefliptt.blueprints.api.schemas import CategorySchema, TaskSchema, Parser, validate_color
from timefliptt.blueprints.base_models import Category, Task


parser = Parser()


class CategoriesView(MethodView):
    def get(self, *args, **kwargs) -> Response:
        """Get the list of categories
        """

        return jsonify(categories=CategorySchema(many=True).dump(Category.query.all()))

    @parser.use_kwargs(CategorySchema(exclude=('id', )), location='json')
    def post(self, name: str) -> Response:
        """Create a new category
        """

        category = Category.create(name)
        db.session.add(category)
        db.session.commit()

        return jsonify(CategorySchema(exclude=('tasks', )).dump(category))


blueprint.add_url_rule('/api/categories/', view_func=CategoriesView.as_view('categories'))


class CategoryView(MethodView):

    class CategorySimpleSchema(Schema):
        id = fields.Integer(required=True, validate=validate.Range(min=0))

        @post_load
        def make_object(self, data, **kwargs):
            return Category.query.get(data['id'])

    @parser.use_args(CategorySimpleSchema, location='view_args')
    def get(self, category: Category, id: int) -> Response:
        """View an existing category
        """

        if category is not None:
            return jsonify(CategorySchema().dump(category))
        else:
            flask.abort(404, description='Unknown category with id={}'.format(id))

    @parser.use_args(CategorySimpleSchema, location='view_args')
    @parser.use_kwargs(TaskSchema(exclude=('id', 'category')), location='json')
    def post(self, category: Category, id: int, name: str, color: str) -> Response:
        """Create a new task in this category
        """

        if category is None:
            flask.abort(404, description='Unknown category with id={}'.format(id))

        task = Task.create(name, category, color)
        db.session.add(task)
        db.session.commit()

        return jsonify(TaskSchema().dump(task))

    @parser.use_args(CategorySimpleSchema, location='view_args')
    @parser.use_kwargs({'name': fields.Str(required=True)}, location='json')
    def put(self, category: Category, id: int, name: str) -> Response:
        """Modify an existing category
        """

        if category is not None:
            category.name = name

            db.session.add(category)
            db.session.commit()

            return jsonify(CategorySchema().dump(category))
        else:
            flask.abort(404, description='Unknown category with id={}'.format(id))

    @parser.use_args(CategorySimpleSchema, location='view_args')
    def delete(self, category: Category, id: int) -> Response:
        """Delete an existing category
        """
        if category is not None:
            db.session.delete(category)
            db.session.commit()
            return jsonify(status='ok')
        else:
            flask.abort(404, description='Unknown category with id={}'.format(id))


blueprint.add_url_rule('/api/categories/<int:id>/', view_func=CategoryView.as_view('category'))


class TasksView(MethodView):
    def get(self, *args, **kwargs) -> Response:
        return jsonify(tasks=TaskSchema(many=True).dump(Task.query.all()))


blueprint.add_url_rule('/api/tasks/', view_func=TasksView.as_view('tasks'))


class TaskView(MethodView):

    class TaskSimpleSchema(Schema):
        id = fields.Integer(required=True, validate=validate.Range(min=0))

        @post_load
        def make_object(self, data, **kwargs):
            return Task.query.get(data['id'])

    @parser.use_args(TaskSimpleSchema, location='view_args')
    def get(self, task: Task, id: int) -> Response:
        """View an existing task
        """

        if task is not None:
            return jsonify(TaskSchema().dump(task))
        else:
            flask.abort(404, description='Unknown task with id={}'.format(id))

    class TaskPutSchema(Schema):
        name = fields.String(validate=validate.Length(min=1))
        color = fields.String(validate=validate_color)
        category = fields.Integer(validate=validate.Range(min=0))

    @parser.use_args(TaskSimpleSchema, location='view_args')
    @parser.use_kwargs(TaskPutSchema, location='json')
    def patch(self, task: Task, id: int, **kwargs) -> Response:
        """Modify an existing task
        """

        if task is not None:
            task.name = kwargs.get('name', task.name)
            task.color = kwargs.get('color', task.color)
            task.category_id = kwargs.get('category', task.category_id)

            db.session.add(task)
            db.session.commit()

            return jsonify(TaskSchema().dump(task))
        else:
            flask.abort(404, description='Unknown task with id={}'.format(id))

    @parser.use_args(TaskSimpleSchema, location='view_args')
    def delete(self, task: Task, id: int) -> Response:
        """Delete an existing task
        """

        if task is not None:
            db.session.delete(task)
            db.session.commit()
            return jsonify(status='ok')
        else:
            flask.abort(404, description='Unknown task with id={}'.format(id))


blueprint.add_url_rule('/api/tasks/<int:id>/', view_func=TaskView.as_view('task'))
