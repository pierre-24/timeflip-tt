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
    def post(self, name) -> Response:
        """Create a new category
        """

        category = Category.create(name)
        db.session.add(category)
        db.session.commit()

        return jsonify(CategorySchema(exclude=('tasks', )).dump(category))


blueprint.add_url_rule('/api/categories/', view_func=CategoriesView.as_view('categories'))


class TasksView(MethodView):
    def get(self, *args, **kwargs) -> Response:
        return jsonify(tasks=TaskSchema(many=True).dump(Task.query.all()))


blueprint.add_url_rule('/api/tasks/', view_func=TasksView.as_view('tasks'))
