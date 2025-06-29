from flask import Blueprint, render_template, request, redirect, url_for
from models import User, Task
from extensions import db

bp = Blueprint('parent', __name__)

@bp.route('/parent', methods=['GET', 'POST'])
def parent():
    users = User.query.filter_by(parent="Shanhu").all()
    selected_user_id = request.args.get('user_id')

    if not selected_user_id and users:
        # Default to the first user in the dropdown if no user_id is provided
        selected_user_id = users[0].id

    selected_user = User.query.get(selected_user_id) if selected_user_id else None
    user_tasks = Task.query.filter_by(user_id=selected_user_id).all() if selected_user_id else []

    if request.method == 'POST':
        action = request.form.get('action')
        user_id = request.form.get('user_id')
        
        if action == 'edit':
            old_task = request.form.get('old_task')
            new_task = request.form.get('new_task')
            frequency = request.form.get('frequency')
            duration = request.form.get('duration')
            task = Task.query.filter_by(user_id=user_id, task=old_task).first()
            if task:
                task.task = new_task
                task.frequency = frequency
                task.duration = int(duration) if duration else None
                db.session.commit()

        elif action == 'delete':
            old_task = request.form.get('old_task')
            task = Task.query.filter_by(user_id=user_id, task=old_task).first()
            if task:
                db.session.delete(task)
                db.session.commit()

        elif action == 'add':
            new_task = request.form.get('task')
            frequency = request.form.get('frequency')
            duration = request.form.get('duration')
            if new_task and frequency:
                task = Task(user_id=user_id, task=new_task, frequency=frequency, duration=int(duration) if duration else None)
                db.session.add(task)
                db.session.commit()

        return redirect(url_for('parent.parent', user_id=user_id))

    return render_template(
        'parent.html',
        users=users,
        selected_user=selected_user,
        user_tasks=user_tasks
    )
