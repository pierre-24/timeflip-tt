import random
from datetime import datetime, timedelta
from tests import FlaskTestCase

from typing import List, Tuple, Any

import flask

from timefliptt.blueprints.base_models import HistoryElement, TimeFlipDevice, Category, Task


class CumulativeTestCase(FlaskTestCase):
    def setUp(self):
        super().setUp()

        self.device = TimeFlipDevice.create('00:00:00:00:00:00', '000000')
        self.db_session.add(self.device)

        num_categories = 3
        self.categories = []
        self.cumulative_time_category = [0] * (num_categories + 1)
        for i in range(num_categories):
            category = Category.create('cat{}'.format(i))
            self.db_session.add(category)
            self.categories.append(category)

        self.db_session.commit()

        self.num_tasks = 10
        self.tasks = []
        self.cumulative_time_task = [0] * (self.num_tasks + 1)
        for i in range(self.num_tasks):
            task = Task.create('x{}'.format(i), self.categories[random.randrange(num_categories)], '#000000')
            self.db_session.add(task)
            self.tasks.append(task)

        self.db_session.commit()

        num_elements = 20
        self.elements = []
        start = datetime.now() - timedelta(minutes=num_elements)
        delta = timedelta(minutes=1)
        for i in range(num_elements):
            end = start + delta
            task = self.tasks[random.randrange(self.num_tasks)]

            self.cumulative_time_task[task.id] += delta.seconds
            self.cumulative_time_category[task.category_id] += delta.seconds

            element = HistoryElement.create(start, end, random.randrange(0, 63), self.device, task)
            self.db_session.add(element)
            self.elements.append(element)
            start = end

        self.db_session.commit()
        self.num_elements = HistoryElement.query.count()

        self.assertEqual(sum(self.cumulative_time_task), self.num_elements * delta.seconds)
        self.assertEqual(sum(self.cumulative_time_category), self.num_elements * delta.seconds)

    def test_cumulative_tasks_ok(self):
        response = self.client.get(flask.url_for('api.statistics-cumulative-tasks'))
        self.assertEqual(response.status_code, 200)
        data = response.get_json()

        # cumulative times match
        for task in data['tasks']:
            self.assertEqual(task['cumulative_time'], self.cumulative_time_task[task['id']])

        # total cumulative time matches
        self.assertEqual(sum(self.cumulative_time_task), data['cumulative_time'])

    def cumulative_tasks(self, args: List[Tuple[str, Any]] = None):
        """Get cumulative for tasks"""

        url = flask.url_for('api.statistics-cumulative-tasks')
        if args is not None:
            url += '?' + '&'.join('{}={}'.format(a, b) for a, b in args)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()

        return data

    def test_filter_task_ok(self):
        self.assertEqual(self.num_elements, HistoryElement.query.count())
        nonzero_ids = [i for i, a in enumerate(self.cumulative_time_task) if a > 0]

        def test(tasks: List[int] = None):
            if tasks is not None:
                expected_ids = list(filter(lambda x: x in tasks, nonzero_ids))
                data = self.cumulative_tasks([('task', i) for i in tasks])
            else:
                expected_ids = nonzero_ids
                data = self.cumulative_tasks()

            cumulative_time = 0
            for task in data['tasks']:
                # task was expected
                self.assertIn(task['id'], expected_ids)

                # cumulative time matches
                self.assertEqual(task['cumulative_time'], self.cumulative_time_task[task['id']])
                cumulative_time += task['cumulative_time']

            # total cumulative time matches
            self.assertEqual(cumulative_time, data['cumulative_time'])

        # all nonzero tasks
        test()

        # all nonzero tasks (explicitly)
        test(nonzero_ids)

        # only one task
        if len(nonzero_ids) > 0:
            test(nonzero_ids[0:1])

        # only two tasks
        if len(nonzero_ids) > 1:
            test(nonzero_ids[0:2])

        # non existing task
        test([Task.query.count() + 1])

    def test_filter_categories_ok(self):
        self.assertEqual(self.num_elements, HistoryElement.query.count())
        nonzero_ids = [i for i, a in enumerate(self.cumulative_time_task) if a > 0]
        nonzero_categories = [i for i, a in enumerate(self.cumulative_time_category) if a > 0]

        def test(categories: List[int] = None):
            if categories is not None:
                expected_ids = list(filter(lambda x: self.tasks[x - 1].category_id in categories, nonzero_ids))
                data = self.cumulative_tasks([('category', i) for i in categories])
            else:
                expected_ids = nonzero_ids
                data = self.cumulative_tasks()

            cumulative_time = 0
            for task in data['tasks']:
                # task was expected
                self.assertIn(task['id'], expected_ids)

                # category match
                if categories is not None:
                    self.assertIn(task['category'], categories)

                # cumulative time matches
                self.assertEqual(task['cumulative_time'], self.cumulative_time_task[task['id']])
                cumulative_time += task['cumulative_time']

            # total cumulative time matches
            self.assertEqual(cumulative_time, data['cumulative_time'])

        # all nonzero categories
        test()

        # all nonzero categories (explicitly)
        test(nonzero_categories)

        # only one category
        if len(nonzero_categories) > 0:
            test(nonzero_categories[0:1])

        # only two category
        if len(nonzero_categories) > 1:
            test(nonzero_categories[0:2])

    def test_filter_start_end_ok(self):
        def test(start: datetime, end: datetime):
            cumulative_time_task = [0] * (self.num_tasks + 1)

            for element in self.elements:
                cumulative_time_task[element.task_id] += element.duration(start, end)

            expected_ids = [i for i, a in enumerate(cumulative_time_task) if a > 0]
            data = self.cumulative_tasks([('start', start.isoformat()), ('end', end.isoformat())])

            for task in data['tasks']:
                # task was expected
                self.assertIn(task['id'], expected_ids)

                # cumulative time matches
                self.assertEqual(task['cumulative_time'], cumulative_time_task[task['id']])

            # total cumulative time matches
            self.assertEqual(sum(cumulative_time_task), data['cumulative_time'])

        # whole range
        test(self.elements[0].start, self.elements[-1].end)

        # part of the range
        test(self.elements[0].start, self.elements[self.num_elements - 5].end)

        # other part of the range
        test(self.elements[-self.num_elements + 5].start, self.elements[-1].end)

        # time frame with no element
        test(self.elements[-1].end + timedelta(seconds=1), self.elements[-1].end + timedelta(minutes=1))

    def test_filter_timeflip_ok(self):
        self.assertEqual(self.num_elements, HistoryElement.query.count())
        nonzero_ids = [i for i, a in enumerate(self.cumulative_time_task) if a > 0]

        def test(devices: List[int] = None):
            if devices is not None:
                expected_ids = [] if self.device.id not in devices else nonzero_ids
                data = self.cumulative_tasks([('timeflip', i) for i in devices])
            else:
                expected_ids = nonzero_ids
                data = self.cumulative_tasks()

            cumulative_time = 0
            for task in data['tasks']:
                # task was expected
                self.assertIn(task['id'], expected_ids)

                # cumulative time matches
                self.assertEqual(task['cumulative_time'], self.cumulative_time_task[task['id']])
                cumulative_time += task['cumulative_time']

            # total cumulative time matches
            self.assertEqual(cumulative_time, data['cumulative_time'])

        # all nonzero tasks
        test()

        # explicit
        test([self.device.id])

        # non-existing device
        test([TimeFlipDevice.query.count() + 1])

    def test_cumulative_category_ok(self):
        response = self.client.get(flask.url_for('api.statistics-cumulative-categories'))
        self.assertEqual(response.status_code, 200)
        data = response.get_json()

        # cumulative times match
        for category in data['categories']:
            self.assertEqual(category['cumulative_time'], self.cumulative_time_category[category['id']])

        # total cumulative time matches
        self.assertEqual(sum(self.cumulative_time_category), data['cumulative_time'])

    def test_cumulative_timeflip_ok(self):
        response = self.client.get(flask.url_for('api.statistics-cumulative-timeflips'))
        self.assertEqual(response.status_code, 200)
        data = response.get_json()

        # cumulative times match
        for device in data['timeflip_devices']:
            self.assertEqual(device['cumulative_time'], sum(self.cumulative_time_category))

        # total cumulative time matches
        self.assertEqual(sum(self.cumulative_time_category), data['cumulative_time'])
