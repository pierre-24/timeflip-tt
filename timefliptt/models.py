from timefliptt.app import db


class BaseModel(db.Model):
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())
    date_modified = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())


class Category(BaseModel):
    name = db.Column(db.VARCHAR(length=150), nullable=False)

    @classmethod
    def create(cls, name: str) -> 'Category':
        o = cls()
        o.name = name

        return o


class Task(BaseModel):

    name = db.Column(db.VARCHAR(length=150), nullable=False)
    facet = db.Column(db.Integer, nullable=True)

    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    category = db.relationship('Category', uselist=False)

    @classmethod
    def create(cls, name: str, category_id: int, facet: int = None) -> 'Task':
        o = cls()
        o.name = name
        o.category_id = category_id
        o.facet = facet

        return o


class HistoryElement(BaseModel):
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)

    task_id = db.Column(db.Integer, db.ForeignKey('task.id', ondelete='SET NULL'))
    task = db.relationship('Task', uselist=False)

    @classmethod
    def create(cls, start_date, end_date, task_id: int = None) -> 'HistoryElement':
        o = cls()

        o.start_date = start_date
        o.end_date = end_date
        o.task_id = task_id

        return o
