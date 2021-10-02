from datetime import datetime, date, timedelta

from typing import Tuple, List

from flask import jsonify, Response
from flask.views import MethodView

from webargs import fields
from marshmallow import Schema, validate, validates_schema, ValidationError

from timefliptt.blueprints.api.views import blueprint
from timefliptt.blueprints.api.schemas import Parser, TaskSchema
from timefliptt.blueprints.base_models import HistoryElement, Task


parser = Parser()


class CumulativeView(MethodView):

    class FilterStatSchema(Schema):
        start = fields.DateTime()
        start_date = fields.Date()
        end = fields.DateTime()
        end_date = fields.Date()

        task = fields.List(fields.Integer(validate=validate.Range(min=0)))
        timeflip = fields.List(fields.Integer(validate=validate.Range(min=0)))
        category = fields.List(fields.Integer(validate=validate.Range(min=0)))

        @validates_schema
        def exclusive_date(self, data, **kwargs):
            if 'start' in data and 'start_date' in data:
                raise ValidationError('cannot define both start and start_date', 'start')

            if 'end' in data and 'end_date' in data:
                raise ValidationError('cannot define both end and end_date', 'end')

    @staticmethod
    def query_elements(**kwargs) -> Tuple[List[HistoryElement], Tuple[datetime, datetime]]:
        """Get the history elements that fit into the filters.
        Returns the list of elements that fulfill the filters and the time frame.

        Note: by default, the time frame is "last 7 days"... Including this one, so it is actually a 8 day period ;)
        """
        query = HistoryElement.query

        # -- Time frame
        start = datetime.combine(date.today(), datetime.min.time()) - timedelta(days=7)
        end = datetime.combine(date.today(), datetime.min.time()) + timedelta(days=1)

        if 'start' in kwargs:
            start = kwargs.get('start')
        elif 'start_date' in kwargs:
            start = datetime.combine(kwargs.get('start_date'), datetime.min.time())

        if 'end' in kwargs:
            end = kwargs.get('end')
        elif 'end_date' in kwargs:
            end = datetime.combine(kwargs.get('end_date'), datetime.min.time())

        if end < start:
            start, end = end, start

        query = query.filter(HistoryElement.end >= start).filter(HistoryElement.start <= end)

        # -- Timeflips
        if 'timeflip' in kwargs:
            query = query.filter(HistoryElement.timeflip_device_id.in_(kwargs.get('timeflip')))

        # -- Tasks
        if 'task' in kwargs:
            query = query.filter(HistoryElement.task_id.in_(kwargs.get('task')))

        # -- Category
        if 'category' in kwargs:
            query = query.join(Task).filter(Task.category_id.in_(kwargs.get('category')))

        return query.all(), (start, end)

    @parser.use_kwargs(FilterStatSchema, location='query')
    def get(self, **kwargs) -> Response:
        """Get cumulative time for each task in a given time frame
        """

        elements, (start, end) = self.query_elements(**kwargs)
        tasks = {}
        cumulative_time = 0

        for element in elements:
            if element.task_id not in tasks:
                tasks[element.task_id] = TaskSchema().dump(element.task)
                tasks[element.task_id]['cumulative_time'] = 0

            duration = element.duration(start, end)
            tasks[element.task_id]['cumulative_time'] = duration
            cumulative_time += duration

        return jsonify(
            start=start.isoformat(),
            end=end.isoformat(),
            tasks=list(tasks.values()),
            cumulative_time=cumulative_time
        )


blueprint.add_url_rule('/api/statistics/cumulative/', view_func=CumulativeView.as_view('statistics-cumulative'))
