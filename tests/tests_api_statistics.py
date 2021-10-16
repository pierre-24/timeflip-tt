import random
import math
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

            self.cumulative_time_task[task.id] += delta.total_seconds()
            self.cumulative_time_category[task.category_id] += delta.total_seconds()

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

    def cumulative_tasks_ok(self, args: List[Tuple[str, Any]] = None):
        """Get cumulative for tasks"""

        url = flask.url_for('api.statistics-cumulative-tasks')
        if args is not None:
            url += '?' + '&'.join('{}={}'.format(a, b) for a, b in args)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()

        return data

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


class PeriodicTestCase(FlaskTestCase):
    def setUp(self):
        super().setUp()

        self.device = TimeFlipDevice.create('00:00:00:00:00:00', '000000')
        self.db_session.add(self.device)

        self.category = Category.create('cat')
        self.db_session.add(self.category)

        self.db_session.commit()

        self.num_tasks = 10
        self.tasks = []
        for i in range(self.num_tasks):
            task = Task.create('x{}'.format(i), self.category, '#000000')
            self.db_session.add(task)
            self.tasks.append(task)

        self.db_session.commit()

        num_elements = 20
        times = random.sample(range(1, 2 * num_elements), num_elements)
        self.elements = []
        self.end = datetime.now()
        self.start = self.end - timedelta(minutes=sum(times))
        start = self.start
        delta = timedelta(minutes=1)
        for i in range(num_elements):
            end = start + times[i] * delta
            task = self.tasks[random.randrange(self.num_tasks)]

            element = HistoryElement.create(start, end, random.randrange(0, 63), self.device, task)
            self.db_session.add(element)
            self.elements.append(element)
            start = end

        self.time_per_tasks = times
        self.db_session.commit()

        self.num_elements = HistoryElement.query.count()

    def test_periodic_tasks(self):
        def cumulative_tasks(start, end: str):
            """For simplicity, I use the cumulative interface as reference (tested above)
            """

            response = self.client.get(
                flask.url_for('api.statistics-cumulative-tasks') + '?start={}&end={}'.format(start, end))
            self.assertEqual(response.status_code, 200)
            return response.get_json()

        period = 525
        response = self.client.get(
            flask.url_for('api.statistics-periodic-tasks', period=period) + '?start={}&end={}'.format(
                self.start.isoformat(), self.end.isoformat())
        )

        self.assertEqual(response.status_code, 200)
        data = response.get_json()

        self.assertEqual((self.end - self.start).total_seconds(), data['cumulative_time'])
        expected_num_periods = int(math.ceil((self.end - self.start).total_seconds() / period))
        self.assertEqual(len(data['periods']), expected_num_periods)

        for period in data['periods']:
            reference = cumulative_tasks(period['start'], period['end'])
            self.assertEqual(reference['cumulative_time'], period['cumulative_time'])  # times match

            reference_task_time = dict((t['id'], t['cumulative_time']) for t in reference['tasks'])
            actual_task_time = dict((t['id'], t['cumulative_time']) for t in period['tasks'])

            for i in reference_task_time:
                self.assertIn(i, actual_task_time)  # the task is there...
                self.assertEqual(reference_task_time[i], actual_task_time[i])  # ... with the same cumulative time!
