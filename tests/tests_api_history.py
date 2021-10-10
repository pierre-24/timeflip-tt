import random
import math
from datetime import datetime, timedelta
from tests import FlaskTestCase

from typing import List

import flask

from timefliptt.blueprints.base_models import HistoryElement, TimeFlipDevice, Category, Task


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

        num_elements = 10
        start = datetime.now() - timedelta(seconds=num_elements)

        self.elements = []

        for i in range(num_elements):
            end = start + timedelta(seconds=1)
            element = HistoryElement.create(start, end, random.randrange(0, 63), self.device)
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
        self.assertEqual(e.task_id, data['task'])
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

    def test_get_history_elements_timeflip_ok(self):
        self.assertEqual(self.num_elements, HistoryElement.query.count())

        response = self.client.get(flask.url_for('api.history-els') + '?timeflip={}'.format(self.device.id))
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(self.num_elements, data['total_elements'])

        response = self.client.get(
            flask.url_for('api.history-els') + '?timeflip={}'.format(TimeFlipDevice.query.count() + 1))
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(0, data['total_elements'])

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
        self.assertEqual(element.task_id, data['task'])
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
        task = self.task

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
        task = self.task

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
