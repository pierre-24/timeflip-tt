from datetime import timedelta
import math

from typing import Tuple, ClassVar, Any, Hashable

import flask
from flask import jsonify, Response
from flask.views import MethodView

from webargs import fields
from marshmallow import Schema, validate

from timefliptt.blueprints.api.views import blueprint
from timefliptt.blueprints.api.schemas import Parser, TaskSchema, CategorySchema, TimeFlipDeviceSchema
from timefliptt.blueprints.base_models import HistoryElement
from timefliptt.blueprints.api.views.views_history import HistoryElementMixin


parser = Parser()


class BaseCumulativeView(HistoryElementMixin, MethodView):

    object_schema: ClassVar[Schema]
    objects_name = 'tasks'

    def discriminate(self, x: HistoryElement) -> Tuple[Hashable, Any]:
        raise NotImplementedError()

    @parser.use_kwargs(HistoryElementMixin.FilterHistoryElementSchema, location='query')
    def get(self, **kwargs) -> Response:
        """Get cumulative time for each task in a given time frame
        """

        elements, (start, end) = self.query_elements(**kwargs)
        schemas = {}
        cumulative_time = 0

        for element in elements.all():
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


class BasePeriodicView(HistoryElementMixin, MethodView):

    object_schema: ClassVar[Schema]
    objects_name: str

    MAX_PERIODS = 100

    def discriminate(self, x: HistoryElement) -> Tuple[Hashable, Any]:
        raise NotImplementedError()

    class PeriodicSchema(Schema):
        period = fields.Integer(validate=validate.Range(min=0), required=True)

    @parser.use_kwargs(PeriodicSchema, location='view_args')
    @parser.use_kwargs(HistoryElementMixin.FilterHistoryElementSchema, location='query')
    def get(self, period: int, **kwargs) -> Response:
        """Get cumulative time for each task in a given period
        """

        elements, (start, end) = self.query_elements(**kwargs)

        num_periods = int(math.ceil((end - start).total_seconds() / period))

        if num_periods > self.MAX_PERIODS:
            flask.abort(
                403,
                description='This request would results in {} periods, which is larger than the limit ({})'.format(
                    num_periods, self.MAX_PERIODS)
            )

        periodic_schemas = []
        accumulator = []
        for i in range(num_periods):
            end_period = start + (i + 1) * timedelta(seconds=period)

            periodic_schemas.append({
                'start': start + i * timedelta(seconds=period),
                'end': end_period if end_period < end else end,
                self.objects_name: {},
                'cumulative_time': 0
            })

            accumulator.append({})

        cumulative_time = 0
        for element in elements.all():
            try:
                discriminant, obj = self.discriminate(element)
            except ValueError:
                continue

            period_start = max(0, int(math.floor((element.start - start).total_seconds() / period)))
            period_end = min(num_periods - 1, int(math.floor((element.end - start).total_seconds() / period)))

            for current_period in range(period_start, period_end + 1):
                if discriminant not in accumulator[current_period]:
                    accumulator[current_period][discriminant] = self.object_schema().dump(obj)
                    accumulator[current_period][discriminant]['cumulative_time'] = 0

                duration = element.duration(
                    periodic_schemas[current_period]['start'], periodic_schemas[current_period]['end'])
                accumulator[current_period][discriminant]['cumulative_time'] += duration
                periodic_schemas[current_period]['cumulative_time'] += duration
                cumulative_time += duration

        for i in range(num_periods):
            periodic_schemas[i][self.objects_name] = list(accumulator[i].values())

            # convert date to isoformat
            periodic_schemas[i]['start'] = periodic_schemas[i]['start'].isoformat()
            periodic_schemas[i]['end'] = periodic_schemas[i]['end'].isoformat()

        return jsonify(**{
            'start': start.isoformat(),
            'end': end.isoformat(),
            'periods': periodic_schemas,
            'cumulative_time': cumulative_time
        })


class PeriodicTaskView(BasePeriodicView):

    objects_name = 'tasks'
    object_schema = TaskSchema

    def discriminate(self, x: HistoryElement) -> Tuple[Hashable, Any]:
        if x.task_id is not None:
            return x.task_id, x.task
        else:
            raise ValueError('x.task_id')


blueprint.add_url_rule(
    '/api/statistics/periodic/<int:period>/tasks/',
    view_func=PeriodicTaskView.as_view('statistics-periodic-tasks')
)


class PeriodicCategoriesView(BasePeriodicView):

    objects_name = 'categories'
    object_schema = CategorySchema

    def discriminate(self, x: HistoryElement) -> Tuple[Hashable, Any]:
        if x.task_id is not None:
            return x.task.category_id, x.task.category
        else:
            raise ValueError('x.task_id')


blueprint.add_url_rule(
    '/api/statistics/periodic/<int:period>/categories/',
    view_func=PeriodicCategoriesView.as_view('statistics-periodic-categories')
)


class PeriodicTimeflipsView(BasePeriodicView):

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
    '/api/statistics/periodic/<int:period>/timeflips/',
    view_func=PeriodicTimeflipsView.as_view('statistics-periodic-timeflips')
)
