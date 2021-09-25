import hashlib
from typing import Union

from flask_login import UserMixin

from timefliptt.app import db


class BaseModel(db.Model):
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())
    date_modified = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())


class User(BaseModel, UserMixin):
    name = db.Column(db.VARCHAR(length=150), nullable=False)
    device_address = db.Column(db.VARCHAR(length=24), nullable=False)
    password_hash = db.Column(db.VARCHAR(length=64), nullable=False)

    @staticmethod
    def hash_pass(password: str) -> str:
        return hashlib.sha512(password.encode()).hexdigest()

    @classmethod
    def create(cls, name: str, address: str, password: str) -> 'User':
        o = cls()
        o.name = name
        o.device_address = address
        o.password_hash = User.hash_pass(password)

        return o

    def is_correct_password(self, password: str) -> bool:
        return self.password_hash == self.hash_pass(password)


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

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', uselist=False)

    task_id = db.Column(db.Integer, db.ForeignKey('task.id'))
    task = db.relationship('Task', uselist=False)

    @classmethod
    def create(cls, user: Union[int, User], facet: int, task: Union[int, Task]) -> 'FacetToTask':
        o = cls()
        o.facet = facet
        o.user_id = user if type(user) is int else user.id
        o.task_id = task if type(task) is int else task.id

        return o


class HistoryElement(BaseModel):
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    original_facet = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'))
    user = db.relationship('User', uselist=False)

    task_id = db.Column(db.Integer, db.ForeignKey('task.id', ondelete='SET NULL'))
    task = db.relationship('Task', uselist=False)

    @classmethod
    def create(
            cls,
            start_date,
            end_date,
            user: Union[int, User],
            task: Union[int, Task],
            comment: str = None
    ) -> 'HistoryElement':
        o = cls()

        o.start_date = start_date
        o.end_date = end_date
        o.user_id = user if type(user) is int else user.int
        o.task_id = task if type(task) is int else task.id
        o.comment = comment

        return o
