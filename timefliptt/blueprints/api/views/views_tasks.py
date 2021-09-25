import flask
from flask import jsonify, Response
from flask.views import MethodView

from webargs import fields

from timefliptt.app import db
from timefliptt.blueprints.api.views import blueprint
from timefliptt.blueprints.api.schemas import CategorySchema, TaskSchema, Parser
from timefliptt.blueprints.base_models import Category, Task


parser = Parser()


class CategoriesView(MethodView):
    def get(self, *args, **kwargs) -> Response:
        """Get the list of categories
        """

        return jsonify(categories=CategorySchema(many=True).dump(Category.query.all()))

    @parser.use_kwargs({'name': fields.Str(required=True)}, location='json')
    def post(self, name: str) -> Response:
        """Create a new category
        """

        category = Category.create(name)
        db.session.add(category)
        db.session.commit()

        return jsonify(CategorySchema(exclude=('tasks', )).dump(category))


blueprint.add_url_rule('/api/categories/', view_func=CategoriesView.as_view('categories'))


class CategoryView(MethodView):

    @parser.use_kwargs({'id': fields.Int(required='true')}, location='view_args')
    def get(self, id: int) -> Response:
        category = Category.query.get(id)

        if category is not None:
            return jsonify(CategorySchema().dump(category))
        else:
            flask.abort(404)

    @parser.use_kwargs({'id': fields.Int(required='true')}, location='view_args')
    @parser.use_kwargs({'name': fields.Str(required=True)}, location='json')
    def put(self, id: int, name: str) -> Response:
        category = Category.query.get(id)

        if category is not None:
            category.name = name

            db.session.add(category)
            db.session.commit()

            return jsonify(CategorySchema().dump(category))
        else:
            flask.abort(404)

    @parser.use_kwargs({'id': fields.Int(required='true')}, location='view_args')
    def delete(self, id: int) -> Response:
        category = Category.query.get(id)

        if category is not None:
            db.session.delete(category)
            db.session.commit()
            return jsonify(status='ok')
        else:
            flask.abort(404)


blueprint.add_url_rule('/api/categories/<int:id>/', view_func=CategoryView.as_view('category'))


class TasksView(MethodView):
    def get(self, *args, **kwargs) -> Response:
        return jsonify(tasks=TaskSchema(many=True).dump(Task.query.all()))


blueprint.add_url_rule('/api/tasks/', view_func=TasksView.as_view('tasks'))
