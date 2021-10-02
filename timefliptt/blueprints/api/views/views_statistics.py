from datetime import datetime, date, timedelta

from typing import Tuple, List, ClassVar, Any, Hashable

from flask import jsonify, Response
from flask.views import MethodView

from webargs import fields
from marshmallow import Schema, validate, validates_schema, ValidationError

from timefliptt.blueprints.api.views import blueprint
from timefliptt.blueprints.api.schemas import Parser, TaskSchema, CategorySchema, TimeFlipDeviceSchema
from timefliptt.blueprints.base_models import HistoryElement, Task


parser = Parser()


class BaseStatisticalView:

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

        query = query.filter(HistoryElement.end > start).filter(HistoryElement.start < end)

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


class BaseCumulativeView(BaseStatisticalView, MethodView):

    object_schema: ClassVar[Schema]
    objects_name = 'tasks'

    def discriminate(self, x: HistoryElement) -> Tuple[Hashable, Any]:
        raise NotImplementedError()

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

    @parser.use_kwargs(FilterStatSchema, location='query')
    def get(self, **kwargs) -> Response:
        """Get cumulative time for each task in a given time frame
        """

        elements, (start, end) = self.query_elements(**kwargs)
        schemas = {}
        cumulative_time = 0

        for element in elements:
            try:
                discriminant, obj = self.discriminate(element)
            except ValueError:
                continue

            if discriminant not in schemas:
                schemas[discriminant] = self.object_schema().dump(obj)
                schemas[discriminant]['cumulative_time'] = 0

            duration = element.duration(start, end)
            schemas[discriminant]['cumulative_time'] += duration
            cumulative_time += duration

        return jsonify(**{
            'start': start.isoformat(),
            'end': end.isoformat(),
            self.objects_name: list(schemas.values()),
            'cumulative_time': cumulative_time
        })


class CumulativeTaskView(BaseCumulativeView):

    objects_name = 'tasks'
    object_schema = TaskSchema

    def discriminate(self, x: HistoryElement) -> Tuple[Hashable, Any]:
        if x.task_id is not None:
            return x.task_id, x.task
        else:
            raise ValueError('x.task_id')


blueprint.add_url_rule(
    '/api/statistics/cumulative/tasks/',
    view_func=CumulativeTaskView.as_view('statistics-cumulative-tasks')
)


class CumulativeCategoriesView(BaseCumulativeView):

    objects_name = 'categories'
    object_schema = CategorySchema

    def discriminate(self, x: HistoryElement) -> Tuple[Hashable, Any]:
        if x.task_id is not None:
            return x.task.category_id, x.task.category
        else:
            raise ValueError('x.task_id')


blueprint.add_url_rule(
    '/api/statistics/cumulative/categories/',
    view_func=CumulativeCategoriesView.as_view('statistics-cumulative-categories')
)


class CumulativeTimeflipsView(BaseCumulativeView):

    objects_name = 'timeflip_devices'
    object_schema = TimeFlipDeviceSchema

    def discriminate(self, x: HistoryElement) -> Tuple[Hashable, Any]:
        """Even though elements are defined without task, only count the ones with one
        """

        if x.task_id is not None:
            return x.timeflip_device_id, x.timeflip_device
        else:
            raise ValueError('x.task_id')


blueprint.add_url_rule(
    '/api/statistics/cumulative/timeflips/',
    view_func=CumulativeTimeflipsView.as_view('statistics-cumulative-timeflips')
)
