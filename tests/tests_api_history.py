import random
import math
from datetime import datetime, timedelta, date
from tests import FlaskTestCase

from typing import List

import flask
from flask.views import MethodView

from timefliptt.blueprints.base_models import HistoryElement, TimeFlipDevice, Category, Task
from timefliptt.blueprints.api.views.views_history import HistoryElementMixin
from timefliptt.blueprints.api.schemas import Parser, HistoryElementSchema


class HistoryElementTestCase(FlaskTestCase):
    def setUp(self):
        super().setUp()

        self.device = TimeFlipDevice.create('00:00:00:00:00:00', '000000')
        self.db_session.add(self.device)
        self.db_session.commit()

    def test_duration(self):
        """Check the behaviour of `duration`
        """

        def h(start: datetime, end: datetime):
            return HistoryElement.create(start, end, 0, self.device)

        base = datetime(2021, 9, 26)
        _1sec = timedelta(seconds=1)
        _1min = timedelta(minutes=1)

        # base
        self.assertEqual(_1sec.seconds, h(base, base + _1sec).duration())
        self.assertEqual(_1min.seconds, h(base, base + _1min).duration())

        # start before
        # -|###|--->
        #    s e
        self.assertEqual(_1sec.seconds, h(base - _1sec, base + _1sec).duration(start=base))

        # end after
        # -|###|--->
        #  s e
        self.assertEqual(_1sec.seconds, h(base - _1sec, base + _1sec).duration(end=base))

        # start before + end after
        # -|#####|--->
        #    s e
        self.assertEqual(_1sec.seconds, h(base - _1min, base + _1min).duration(start=base, end=base + _1sec))

        # outside range (before)
        # -|###|----->
        #        s e
        self.assertEqual(0, h(base - _1min, base - _1sec).duration(start=base))

        # outside range (after)
        # -----|###|--->
        #  s e
        self.assertEqual(0, h(base + _1sec, base + _1min).duration(end=base))


class HistoryElementMixinCase(FlaskTestCase):

    def setUp(self):
        super().setUp()

        class FakeView(HistoryElementMixin, MethodView):

            parser = Parser()

            @parser.use_kwargs(HistoryElementMixin.FilterHistoryElementSchema, location='query')
            def get(self, **kwargs):
                """Get the list of history elements
                """

                elements, (start, end) = self.query_elements(**kwargs)

                return flask.jsonify(
                    elements=HistoryElementSchema(many=True).dump(elements.all()),
                    start=start.isoformat(),
                    end=end.isoformat()
                )

        self.app.add_url_rule('/api/whatever/the/fuck/', view_func=FakeView.as_view('test'))

        self.device = TimeFlipDevice.create('00:00:00:00:00:00', '000000')
        self.db_session.add(self.device)

        self.num_categories = 3
        self.categories = []
        for i in range(self.num_categories):
            category = Category.create('cat{}'.format(i))
            self.db_session.add(category)
            self.categories.append(category)

        self.db_session.commit()

        self.num_tasks = 10
        self.tasks = []
        for i in range(self.num_tasks):
            task = Task.create('x{}'.format(i), self.categories[random.randrange(self.num_categories)], '#000000')
            self.db_session.add(task)
            self.tasks.append(task)

        self.db_session.commit()

        num_elements = 20
        self.elements = []
        self.start = datetime.now() - timedelta(minutes=num_elements)
        start = self.start
        delta = timedelta(days=1)
        for i in range(num_elements):
            end = start + delta
            task = self.tasks[random.randrange(self.num_tasks)]

            element = HistoryElement.create(start, end, random.randrange(0, 63), self.device, task)
            self.db_session.add(element)
            self.elements.append(element)
            start = end

        self.db_session.commit()
        self.num_elements = HistoryElement.query.count()

    def test_filter_start_end_date_ok(self):

        def test(start: date = date.min, end: date = date.max):
            elements, (s, e) = HistoryElementMixin.query_elements(start_date=start, end_date=end)

            self.assertEqual(s.date(), start)
            self.assertEqual(e.date(), end)

            elements = elements.all()
            actual_elements = list(filter(lambda e: e.start.date() < end and e.end.date() >= start, self.elements))

            self.assertEqual(len(elements), len(actual_elements))
            for element in actual_elements:
                self.assertIn(element, elements)

            response = self.client.get(
                flask.url_for('test') + '?start_date={}&end_date={}'.format(start.isoformat(), end.isoformat()))
            self.assertEqual(response.status_code, 200)
            data = response.get_json()

            actual_elements_id = [e.id for e in actual_elements]
            for i in map(lambda e: e['id'], data['elements']):
                self.assertIn(i, actual_elements_id)

        # test all element
        test()

        # test with no element
        test(end=self.start.date())

        # test with some elements
        test(start=self.elements[self.num_elements - 10].start.date())
        test(end=self.elements[self.num_elements - 10].end.date())

    def test_filter_start_end_ok(self):

        def test(start: datetime = datetime.min, end: datetime = datetime.max):
            elements, (s, e) = HistoryElementMixin.query_elements(start=start, end=end)

            self.assertEqual(s, start)
            self.assertEqual(e, end)

            elements = elements.all()
            actual_elements = list(filter(lambda e: e.start < end and e.end > start, self.elements))

            self.assertEqual(len(elements), len(actual_elements))
            for element in actual_elements:
                self.assertIn(element, elements)

            response = self.client.get(
                flask.url_for('test') + '?start={}&end={}'.format(start.isoformat(), end.isoformat()))
            self.assertEqual(response.status_code, 200)
            data = response.get_json()

            actual_elements_id = [e.id for e in actual_elements]
            for i in map(lambda e: e['id'], data['elements']):
                self.assertIn(i, actual_elements_id)

        # test all element
        test()

        # test with no element
        test(end=self.start)

        # test with some elements
        test(start=self.elements[self.num_elements - 10].start)
        test(end=self.elements[self.num_elements - 10].end)

    def test_filter_tasks_ok(self):
        def test(tasks: List[int] = None):
            actual_elements = self.elements

            kwargs = {}
            if tasks is not None:
                kwargs['task'] = tasks
                actual_elements = list(filter(lambda e: e.task_id in tasks, self.elements))

            elements, _ = HistoryElementMixin.query_elements(**kwargs)
            elements = elements.all()

            self.assertEqual(len(elements), len(actual_elements))
            for element in actual_elements:
                self.assertIn(element, elements)

            url = flask.url_for('test')
            if tasks is not None and len(tasks) > 0:
                url += '?task={}'.format('&task='.join(str(t) for t in tasks))

            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            data = response.get_json()

            actual_elements_id = [e.id for e in actual_elements]
            for i in map(lambda e: e['id'], data['elements']):
                self.assertIn(i, actual_elements_id)

        # test all
        test()

        # test none
        test([self.num_elements + 1])

        # test with some
        test([t.id for t in self.tasks[:4]])

    def test_filter_categories_ok(self):
        def test(categories: List[int] = None):
            actual_elements = self.elements

            kwargs = {}
            if categories is not None:
                kwargs['category'] = categories
                actual_elements = list(filter(lambda e: e.task.category_id in categories, self.elements))

            elements, _ = HistoryElementMixin.query_elements(**kwargs)
            elements = elements.all()

            self.assertEqual(len(elements), len(actual_elements))
            for element in actual_elements:
                self.assertIn(element, elements)

            url = flask.url_for('test')
            if categories is not None and len(categories) > 0:
                url += '?category={}'.format('&category='.join(str(t) for t in categories))

            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            data = response.get_json()

            actual_elements_id = [e.id for e in actual_elements]
            for i in map(lambda e: e['id'], data['elements']):
                self.assertIn(i, actual_elements_id)

        # test all
        test()

        # test none
        test([self.num_categories + 1])

        # test with some
        test([t.id for t in self.categories[:2]])

    def test_filter_timeflip(self):
        def test(timeflips: List[int] = None):
            actual_elements = self.elements

            kwargs = {}
            if timeflips is not None:
                kwargs['category'] = timeflips
                if self.device.id not in timeflips:
                    actual_elements = []

            elements, _ = HistoryElementMixin.query_elements(**kwargs)
            elements = elements.all()

            self.assertEqual(len(elements), len(actual_elements))
            for element in actual_elements:
                self.assertIn(element, elements)

            url = flask.url_for('test')
            if timeflips is not None and len(timeflips) > 0:
                url += '?timeflip={}'.format('&timeflip='.join(str(t) for t in timeflips))

            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            data = response.get_json()

            actual_elements_id = [e.id for e in actual_elements]
            for i in map(lambda e: e['id'], data['elements']):
                self.assertIn(i, actual_elements_id)

        # test all
        test()

        # test none
        test([self.device.id + 5])

    def test_negative_task_ko(self):
        response = self.client.get(flask.url_for('test') + '?task=-1')
        self.assertEqual(response.status_code, 422)

    def test_negative_category_ko(self):
        response = self.client.get(flask.url_for('test') + '?category=-1')
        self.assertEqual(response.status_code, 422)

    def test_negative_timeflip_ko(self):
        response = self.client.get(flask.url_for('test') + '?timeflip=-1')
        self.assertEqual(response.status_code, 422)


class HistoryTestCase(FlaskTestCase):
    def setUp(self):
        super().setUp()

        self.category = Category.create('x')
        self.db_session.add(self.category)

        self.device = TimeFlipDevice.create('00:00:00:00:00:00', '000000')
        self.db_session.add(self.device)
        self.db_session.commit()

        self.task = Task.create('x', self.category, '#000000')
        self.db_session.add(self.task)
        self.other_task = Task.create('y', self.category, '#000000')
        self.db_session.add(self.other_task)

        num_elements = 10
        start = datetime.now() - timedelta(seconds=num_elements)

        self.elements = []

        for i in range(num_elements):
            end = start + timedelta(seconds=1)
            element = HistoryElement.create(start, end, random.randrange(0, 63), self.device, self.task)
            self.db_session.add(element)
            self.elements.append(element)
            start = end

        self.db_session.commit()

        self.num_elements = HistoryElement.query.count()

    def test_get_history_elements_ok(self):
        self.assertEqual(self.num_elements, HistoryElement.query.count())

        def elmts(page: int, page_size: int = 5, expected_status: int = 200) -> List[dict]:
            response = self.client.get(
                flask.url_for('api.history-els') + '?page={}&page_size={}'.format(page, page_size))
            self.assertEqual(response.status_code, expected_status)
            if response.status_code == 200:
                data = response.get_json()

                self.assertEqual(data['current_page'], page)
                self.assertEqual(data['page_size'], page_size)

                return data['history']
            else:
                return []

        # test content
        data = elmts(0)[0]

        e = HistoryElement.query.order_by(HistoryElement.id.desc()).first()
        self.assertEqual(e.id, data['id'])
        self.assertEqual(e.original_facet, data['original_facet'])
        self.assertEqual(e.timeflip_device_id, data['timeflip_device'])
        self.assertEqual(e.comment, data['comment'])
        self.assertEqual(e.task_id, data['task']['id'])
        self.assertEqual(e.start.isoformat(), data['start'])
        self.assertEqual(e.end.isoformat(), data['end'])

        # test page size
        self.assertEqual(len(elmts(0, 5)), 5)
        self.assertEqual(len(elmts(0, 2)), 2)

        # test pagination
        page_size = 4
        for i in range(int(math.ceil(self.num_elements / page_size))):
            start = self.num_elements - i * page_size
            end = max(start - page_size, 0)

            self.assertEqual(list(e['id'] for e in elmts(i, page_size)), list(range(start, end, -1)))

        # test outside bond (get 404)
        self.assertEqual(len(elmts(self.num_elements + 1, 1, expected_status=404)), 0)
        self.assertEqual(len(elmts(-2, 1, expected_status=422)), 0)

    def test_get_history_element_ok(self):
        self.assertEqual(self.num_elements, HistoryElement.query.count())
        element = self.elements[0]

        response = self.client.get(flask.url_for('api.history-el', id=element.id))
        self.assertEqual(response.status_code, 200)
        data = response.get_json()

        self.assertEqual(element.id, data['id'])
        self.assertEqual(element.original_facet, data['original_facet'])
        self.assertEqual(element.timeflip_device_id, data['timeflip_device'])
        self.assertEqual(element.comment, data['comment'])
        self.assertEqual(element.task_id, data['task']['id'])
        self.assertEqual(element.start.isoformat(), data['start'])
        self.assertEqual(element.end.isoformat(), data['end'])

    def test_get_unknown_history_element_ko(self):
        self.assertEqual(self.num_elements, HistoryElement.query.count())

        response = self.client.get(flask.url_for('api.history-el', id=self.num_elements + 1))
        self.assertEqual(response.status_code, 404)

    def test_modify_history_element_ok(self):
        self.assertEqual(self.num_elements, HistoryElement.query.count())
        element = self.elements[0]

        comment = 'whatever'
        task = self.other_task

        start = datetime.now() - timedelta(seconds=100)
        end = start + timedelta(seconds=1)

        response = self.client.patch(flask.url_for('api.history-el', id=element.id), json={
            'comment': comment,
            'task': task.id,
            'start': start.isoformat(),
            'end': end.isoformat()
        })
        self.assertEqual(response.status_code, 200)

        data = response.get_json()
        self.assertEqual(comment, data['comment'])
        self.assertEqual(task.id, data['task']['id'])
        self.assertEqual(start.isoformat(), data['start'])
        self.assertEqual(end.isoformat(), data['end'])

        e = HistoryElement.query.get(element.id)
        self.assertEqual(comment, e.comment)
        self.assertEqual(task.id, e.task_id)
        self.assertEqual(start, e.start)
        self.assertEqual(end, e.end)

    def test_modify_history_element_negative_task_ok(self):
        self.assertEqual(self.num_elements, HistoryElement.query.count())
        element = self.elements[0]

        response = self.client.patch(flask.url_for('api.history-el', id=element.id), json={
            'task': -1  # negative id remove task
        })
        self.assertEqual(response.status_code, 200)

        data = response.get_json()
        self.assertIsNone(data['task'])

        e = HistoryElement.query.get(element.id)
        self.assertIsNone(e.task_id)

    def test_modify_unknown_history_element_ko(self):
        self.assertEqual(self.num_elements, HistoryElement.query.count())

        response = self.client.patch(flask.url_for('api.history-el', id=self.num_elements + 1))
        self.assertEqual(response.status_code, 404)

    def test_modify_history_element_unknown_task_ko(self):
        self.assertEqual(self.num_elements, HistoryElement.query.count())
        element = self.elements[0]

        response = self.client.patch(flask.url_for('api.history-el', id=element.id), json={
            'task': Task.query.count() + 1
        })
        self.assertEqual(response.status_code, 404)

    def test_delete_history_element_ok(self):
        self.assertEqual(self.num_elements, HistoryElement.query.count())
        element = self.elements[0]

        response = self.client.delete(flask.url_for('api.history-el', id=element.id))
        self.assertEqual(response.status_code, 200)

        self.assertEqual(self.num_elements - 1, HistoryElement.query.count())
        self.assertIsNone(HistoryElement.query.get(element.id))

    def test_delete_unknown_history_element_ko(self):
        self.assertEqual(self.num_elements, HistoryElement.query.count())

        response = self.client.delete(flask.url_for('api.history-el', id=self.num_elements + 1))
        self.assertEqual(response.status_code, 404)

        self.assertEqual(self.num_elements, HistoryElement.query.count())

    def test_delete_history_elements_batch_ok(self):
        self.assertEqual(self.num_elements, HistoryElement.query.count())
        elements = self.elements[0:2]

        response = self.client.delete(
            flask.url_for('api.history-els') + '?' + '&'.join('id={}'.format(e.id) for e in elements))
        self.assertEqual(response.status_code, 200)

        self.assertEqual(self.num_elements - len(elements), HistoryElement.query.count())
        for e in elements:
            self.assertIsNone(HistoryElement.query.get(e.id))

    def test_delete_unknown_history_elements_batch_ko(self):
        self.assertEqual(self.num_elements, HistoryElement.query.count())

        response = self.client.delete(flask.url_for('api.history-els') + '?id={}'.format(self.num_elements + 1))
        self.assertEqual(response.status_code, 404)

        self.assertEqual(self.num_elements, HistoryElement.query.count())

    def test_modify_history_elements_batch_ok(self):
        self.assertEqual(self.num_elements, HistoryElement.query.count())
        elements = self.elements[0:2]

        comment = 'whatever'
        task = self.other_task

        response = self.client.patch(
            flask.url_for('api.history-els') + '?' + '&'.join('id={}'.format(e.id) for e in elements), json={
                'comment': comment,
                'task': task.id
            })
        self.assertEqual(response.status_code, 200)

        data = response.get_json()
        for element in data:
            self.assertEqual(comment, element['comment'])
            self.assertEqual(task.id, element['task']['id'])

        for element in elements:
            e = HistoryElement.query.get(element.id)
            self.assertEqual(comment, e.comment)
            self.assertEqual(task.id, e.task_id)

    def test_modify_history_elements_negative_task_batch_ok(self):
        self.assertEqual(self.num_elements, HistoryElement.query.count())
        elements = self.elements[0:2]

        response = self.client.patch(
            flask.url_for('api.history-els') + '?' + '&'.join('id={}'.format(e.id) for e in elements), json={
                'task': -1  # negative id remove task
            })
        self.assertEqual(response.status_code, 200)

        data = response.get_json()
        for element in data:
            self.assertIsNone(element['task'])

        for element in elements:
            e = HistoryElement.query.get(element.id)
            self.assertIsNone(e.task_id)

    def test_modify_unknown_history_elements_batch_ko(self):
        self.assertEqual(self.num_elements, HistoryElement.query.count())

        response = self.client.patch(flask.url_for('api.history-els') + '?id={}'.format(self.num_elements + 1))
        self.assertEqual(response.status_code, 404)

    def test_modify_history_elements_batch_unknown_task_ko(self):
        self.assertEqual(self.num_elements, HistoryElement.query.count())
        elements = self.elements[0:2]

        response = self.client.patch(
            flask.url_for('api.history-els') + '?' + '&'.join('id={}'.format(e.id) for e in elements), json={
                'task': Task.query.count() + 1
            })
        self.assertEqual(response.status_code, 404)

    def test_delete_task_does_not_delete_history_ok(self):
        self.assertEqual(self.num_elements, HistoryElement.query.count())

        self.db_session.delete(self.task)
        self.db_session.commit()

        self.assertEqual(self.num_elements, HistoryElement.query.count())
        self.assertIsNone(HistoryElement.query.first().task_id)

    def test_delete_device_does_not_delete_history_ok(self):
        self.assertEqual(self.num_elements, HistoryElement.query.count())

        self.db_session.delete(self.device)
        self.db_session.commit()

        self.assertEqual(self.num_elements, HistoryElement.query.count())
        self.assertIsNone(HistoryElement.query.first().timeflip_device_id)
