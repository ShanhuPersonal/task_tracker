from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)  # Auto-incrementing ID
    name = db.Column(db.String(50), nullable=False)
    dob = db.Column(db.String(10), nullable=False)  # Format: YYYY-MM-DD
    ai_difficulty = db.Column(db.Integer, nullable=False)
    parent = db.Column(db.String(50), nullable=False)

    # Relationship to tasks and task_logs
    tasks = db.relationship('Task', backref='user', lazy=True)
    task_logs = db.relationship('TaskLog', backref='user', lazy=True)

class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Foreign key to users.id
    task = db.Column(db.String(200), nullable=False)
    frequency = db.Column(db.String(50), nullable=False)

class TaskLog(db.Model):
    __tablename__ = 'task_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Foreign key to users.id
    task = db.Column(db.String(200), nullable=False)
    date = db.Column(db.String(10), nullable=False)  # Format: YYYY-MM-DD
    status = db.Column(db.String(10), nullable=False)  # "Done" or "TODO"
    time = db.Column(db.String(8), nullable=True)  # Format: HH:MM:SS