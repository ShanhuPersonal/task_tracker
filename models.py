from extensions import db
from sqlalchemy import Integer

class Parent(db.Model):
    __tablename__ = 'parents'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    
    # Relationship to users
    users = db.relationship('User', backref='parent_ref', lazy=True)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    dob = db.Column(db.String(10), nullable=False)
    ai_difficulty = db.Column(db.Integer, nullable=False, default=10)
    parent_id = db.Column(db.Integer, db.ForeignKey('parents.id'), nullable=False)

class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    task = db.Column(db.String(200), nullable=False)
    frequency = db.Column(db.String(50), nullable=False)
    duration = db.Column(Integer, nullable=True)  # Duration in minutes, default is empty
    log_completed_page_numbers = db.Column(db.Boolean, nullable=False, default=False)  # Whether to log page numbers

class TaskLog(db.Model):
    __tablename__ = 'task_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    task = db.Column(db.String(200), nullable=False)
    date = db.Column(db.String(10), nullable=False)
    status = db.Column(db.String(10), nullable=False)
    time = db.Column(db.String(8), nullable=True)
    completed_page_numbers = db.Column(db.String(200), nullable=True)  # Page numbers completed
