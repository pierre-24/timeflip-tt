from typing import Union
from datetime import datetime

from timefliptt.app import db


class BaseModel(db.Model):
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())
    date_modified = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())


class TimeFlipDevice(BaseModel):

    __tablename__ = 'timeflip_device'

    name = db.Column(db.VARCHAR(length=150), nullable=False)
    address = db.Column(db.VARCHAR(length=24), nullable=False)
    password = db.Column(db.VARCHAR(length=6), nullable=False)

    @classmethod
    def create(cls, name: str, address: str, password: str) -> 'TimeFlipDevice':
        o = cls()
        o.name = name
        o.address = address
        o.password = password

        return o


class Category(BaseModel):
    name = db.Column(db.VARCHAR(length=150), nullable=False)

    tasks = db.relationship('Task', back_populates='category')

    @classmethod
    def create(cls, name: str) -> 'Category':
        o = cls()
        o.name = name

        return o


class Task(BaseModel):

    name = db.Column(db.VARCHAR(length=150), nullable=False)
    color = db.Column(db.VARCHAR(length=7), nullable=False)

    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    category = db.relationship('Category', uselist=False, back_populates='tasks')

    @classmethod
    def create(cls, name: str, category: Union[int, Category], color: str) -> 'Task':
        o = cls()
        o.name = name
        o.category_id = category if type(category) is int else category.id
        o.color = color

        return o


class FacetToTask(BaseModel):

    facet = db.Column(db.Integer, nullable=False)

    timeflip_device_id = db.Column(db.Integer, db.ForeignKey('timeflip_device.id'))
    timeflip_device = db.relationship('TimeFlipDevice', uselist=False)

    task_id = db.Column(db.Integer, db.ForeignKey('task.id'))
    task = db.relationship('Task', uselist=False)

    @classmethod
    def create(cls, device: Union[int, TimeFlipDevice], facet: int, task: Union[int, Task]) -> 'FacetToTask':
        o = cls()
        o.facet = facet
        o.timeflip_device_id = device if type(device) is int else device.id
        o.task_id = task if type(task) is int else task.id

        return o


class HistoryElement(BaseModel):
    start = db.Column(db.DateTime, nullable=False)
    end = db.Column(db.DateTime, nullable=False)
    original_facet = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)

    timeflip_device_id = db.Column(db.Integer, db.ForeignKey('timeflip_device.id', ondelete='SET NULL'))
    timeflip_device = db.relationship('TimeFlipDevice', uselist=False)

    task_id = db.Column(db.Integer, db.ForeignKey('task.id', ondelete='SET NULL'))
    task = db.relationship('Task', uselist=False)

    @classmethod
    def create(
            cls,
            start: datetime,
            end: datetime,
            device: Union[int, TimeFlipDevice],
            task: Union[int, Task],
            comment: str = None
    ) -> 'HistoryElement':
        o = cls()

        if start > end:
            raise ValueError('start > end')

        o.start = start
        o.end = end
        o.timeflip_device_id = device if type(device) is int else device.id
        o.task_id = task if type(task) is int else task.id
        o.comment = comment

        return o

    def duration(self, start: datetime = None, end: datetime = None) -> int:
        """Get the duration within time frame if any.
        `start=None` is equivalent to `start=datetime.min` and `end=None` is equivalent to `end=datetime.max`
        """

        if start is None:
            start = datetime.min

        if end is None:
            end = datetime.max

        if start > end:
            raise ValueError('start > end')

        if start > self.end or end < self.start:
            return 0
        else:
            return (min(end, self.end) - max(start, self.start)).seconds
