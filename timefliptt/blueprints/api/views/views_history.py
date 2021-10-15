import math

from typing import List

import flask
from flask import jsonify, Response
from flask.views import MethodView

from webargs import fields
from marshmallow import Schema, validate, post_load

from timefliptt.app import db
from timefliptt.blueprints.api.views import blueprint
from timefliptt.blueprints.api.schemas import HistoryElementSchema, Parser
from timefliptt.blueprints.base_models import HistoryElement, Task


parser = Parser()


class HistoryElementsView(MethodView):
    PAGE_SIZE = 5

    class PaginateSchema(Schema):
        page = fields.Integer(validate=validate.Range(min=0))
        page_size = fields.Integer(validate=validate.Range(min=0))
        timeflip = fields.Integer(validate=validate.Range(min=0))

    @parser.use_kwargs(PaginateSchema, location='query')
    def get(self, **kwargs) -> Response:
        """Get the list of history elements
        """

        page = kwargs.get('page', 0)
        page_size = kwargs.get('page_size', self.PAGE_SIZE)

        query = HistoryElement\
            .query\
            .order_by(HistoryElement.id.desc())

        if 'timeflip' in kwargs:
            query = query.filter(HistoryElement.timeflip_device_id.is_(kwargs.get('timeflip')))

        num_results = query.count()
        if page < 0 or page * page_size > num_results:
            flask.abort(404)

        results = query.slice(page * page_size, (page + 1) * page_size).all()

        FORMAT = '{}?page={}&page_size={}'

        previous_page = None
        if page > 0:
            previous_page = FORMAT.format(flask.url_for('api.history-els'), page - 1, page_size)
        next_page = None
        if num_results > 0 and (page + 1) * page_size < num_results:
            next_page = FORMAT.format(flask.url_for('api.history-els'), page + 1, page_size)

        return jsonify(
            total_elements=num_results,
            total_pages=int(math.ceil(num_results / page_size)),
            current_page=page,
            page_size=page_size,
            previous_page=previous_page,
            next_page=next_page,
            history=HistoryElementSchema(many=True).dump(results)
        )

    class SimpleHistoryElementsSchema(Schema):
        id = fields.List(fields.Integer(validate=validate.Range(min=0)))

        @post_load
        def make_objects(self, data, **kwargs):
            return HistoryElement.query.filter(HistoryElement.id.in_(data['id'])).all()

    class ModifyHistorySchema(Schema):
        task = fields.Integer()
        comment = fields.Str()

    @parser.use_args(SimpleHistoryElementsSchema, location='query')
    @parser.use_kwargs(ModifyHistorySchema, location='json')
    def patch(self, elements: List[HistoryElement], **kwargs) -> Response:
        if len(elements) > 0:
            if 'task' in kwargs:
                task_id = kwargs.get('task')
                if task_id >= 0:
                    task = Task.query.get(task_id)
                    if task is None:
                        flask.abort(404, description='Unknown task with id={}'.format(kwargs.get('task')))

                    for element in elements:
                        element.task_id = task.id
                        db.session.add(element)
                else:
                    for element in elements:
                        element.task_id = None
                        db.session.add(element)

            if 'comment' in kwargs:
                for element in elements:
                    element.comment = kwargs.get('comment')
                    db.session.add(element)

            db.session.commit()
            return jsonify(HistoryElementSchema(many=True).dump(elements))
        else:
            flask.abort(404, description='Unknown elements')

    @parser.use_args(SimpleHistoryElementsSchema, location='query')
    def delete(self, elements: List[HistoryElement], **kwargs) -> Response:
        if len(elements) > 0:
            for e in elements:
                db.session.delete(e)

            db.session.commit()
            return jsonify(status='ok')
        else:
            flask.abort(404, description='Unknown elements')


blueprint.add_url_rule('/api/history/', view_func=HistoryElementsView.as_view('history-els'))


class HistoryElementView(MethodView):

    class SimpleHistoryElementSchema(Schema):
        id = fields.Integer(validate=validate.Range(min=0))

        @post_load
        def make_object(self, data, **kwargs):
            return HistoryElement.query.get(data['id'])

    @parser.use_args(SimpleHistoryElementSchema, location='view_args')
    def get(self, element: HistoryElement, id: int) -> Response:
        if element is not None:
            return jsonify(HistoryElementSchema().dump(element))
        else:
            flask.abort(404, description='Unknown element with id={}'.format(id))

    class ModifyHistorySchema(Schema):
        task = fields.Integer()
        comment = fields.Str()
        start = fields.DateTime()
        end = fields.DateTime()

    @parser.use_args(SimpleHistoryElementSchema, location='view_args')
    @parser.use_kwargs(ModifyHistorySchema, location='json')
    def patch(self, element: HistoryElement, id: int, **kwargs) -> Response:
        if element is not None:
            if 'task' in kwargs:
                task_id = kwargs.get('task')
                if task_id >= 0:
                    task = Task.query.get(kwargs.get('task'))
                    if task is None:
                        flask.abort(404, description='Unknown task with id={}'.format(kwargs.get('task')))

                    element.task_id = task.id
                else:
                    element.task_id = None

            els = ['comment', 'start', 'end']
            for el in els:
                if el in kwargs:
                    setattr(element, el, kwargs.get(el))

            db.session.add(element)
            db.session.commit()
            return jsonify(HistoryElementSchema().dump(element))
        else:
            flask.abort(404, description='Unknown element with id={}'.format(id))

    @parser.use_args(SimpleHistoryElementSchema, location='view_args')
    def delete(self, element: HistoryElement, id: int) -> Response:
        if element is not None:
            db.session.delete(element)
            db.session.commit()
            return jsonify(status='ok')
        else:
            flask.abort(404, description='Unknown element with id={}'.format(id))


blueprint.add_url_rule('/api/history/<int:id>/', view_func=HistoryElementView.as_view('history-el'))
