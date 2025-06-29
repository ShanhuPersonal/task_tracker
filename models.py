from extensions import db
from sqlalchemy import Integer

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    dob = db.Column(db.String(10), nullable=False)
    ai_difficulty = db.Column(db.Integer, nullable=False, default=10)
    parent = db.Column(db.String(50), nullable=False)

class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    task = db.Column(db.String(200), nullable=False)
    frequency = db.Column(db.String(50), nullable=False)
    duration = db.Column(Integer, nullable=True)  # Duration in minutes, default is empty

class TaskLog(db.Model):
    __tablename__ = 'task_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    task = db.Column(db.String(200), nullable=False)
    date = db.Column(db.String(10), nullable=False)
    status = db.Column(db.String(10), nullable=False)
    time = db.Column(db.String(8), nullable=True)
