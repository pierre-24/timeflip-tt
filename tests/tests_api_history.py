import random
import math
from datetime import datetime, timedelta
from tests import FlaskTestCase

from typing import List

import flask

from timefliptt.blueprints.base_models import HistoryElement, TimeFlipDevice


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

        self.device = TimeFlipDevice.create('00:00:00:00:00:00', '000000')
        self.db_session.add(self.device)
        self.db_session.commit()

        num_elements = 10
        start = datetime.now() - timedelta(seconds=num_elements)

        for i in range(num_elements):
            end = start + timedelta(seconds=1)
            element = HistoryElement.create(start, end, random.randrange(0, 63), self.device)
            self.db_session.add(element)
            start = end

        self.db_session.commit()

        self.num_elements = HistoryElement.query.count()

    def test_get_history_ok(self):
        self.assertEqual(self.num_elements, HistoryElement.query.count())

        def elmts(page: int, page_size: int = 5, expected_status: int = 200) -> List[dict]:
            response = self.client.get(flask.url_for('api.histories') + '?page={}&page_size={}'.format(page, page_size))
            self.assertEqual(response.status_code, expected_status)
            if response.status_code == 200:
                return response.get_json()['history']
            else:
                return []

        # test content
        data = elmts(0)[0]

        e = HistoryElement.query.order_by(HistoryElement.id.desc()).first()
        self.assertEqual(e.id, data['id'])
        self.assertEqual(e.original_facet, data['original_facet'])
        self.assertEqual(e.timeflip_device_id, data['timeflip_device'])
        self.assertEqual(e.comment, data['comment'])

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
        self.assertEqual(len(elmts(-2, 1, expected_status=404)), 0)
