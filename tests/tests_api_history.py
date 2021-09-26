from datetime import datetime, timedelta
from tests import FlaskTestCase

from timefliptt.blueprints.base_models import HistoryElement, Category, TimeFlipDevice, Task


class HistoryTestCase(FlaskTestCase):
    def setUp(self):
        super().setUp()

        self.category = Category.create('test1')
        self.db_session.add(self.category)

        self.device = TimeFlipDevice.create('TF', '00:00:00:00:00:00', '000000')
        self.db_session.add(self.device)
        self.db_session.commit()

        self.num_devices = TimeFlipDevice.query.count()

        self.task_1 = Task.create('test1', self.category, '#ffffff')
        self.db_session.add(self.task_1)
        self.task_2 = Task.create('test2', self.category, '#ffffff')
        self.db_session.add(self.task_2)
        self.db_session.commit()

    def test_duration(self):
        """Check the behaviour of `duration`
        """

        def h(start: datetime, end: datetime):
            return HistoryElement.create(start, end, self.device, self.task_1)

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
