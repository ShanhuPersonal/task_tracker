from flask import Blueprint, render_template, request, redirect, url_for
from models import User, Task, Parent
from extensions import db

bp = Blueprint('parent', __name__)

@bp.route('/parent', methods=['GET', 'POST'])
def parent():
    # Get the parent by name (could be made dynamic later)
    parent_obj = Parent.query.filter_by(name="Shanhu").first()
    if not parent_obj:
        # Create parent if it doesn't exist
        parent_obj = Parent(name="Shanhu")
        db.session.add(parent_obj)
        db.session.commit()
    
    users = User.query.filter_by(parent_id=parent_obj.id).all()
    selected_user_id = request.args.get('user_id')
    error_message = request.args.get('error')

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
            log_page_numbers = request.form.get('log_completed_page_numbers') == 'on'
            task = Task.query.filter_by(user_id=user_id, task=old_task).first()
            if task:
                task.task = new_task
                task.frequency = frequency
                task.duration = int(duration) if duration else None
                task.log_completed_page_numbers = log_page_numbers
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
            log_page_numbers = request.form.get('log_completed_page_numbers') == 'on'
            if new_task and frequency:
                task = Task(user_id=user_id, task=new_task, frequency=frequency, 
                           duration=int(duration) if duration else None,
                           log_completed_page_numbers=log_page_numbers)
                db.session.add(task)
                db.session.commit()
        
        elif action == 'edit_user':
            user_id = request.form.get('edit_user_id')
            name = request.form.get('user_name')
            dob = request.form.get('user_dob')
            ai_difficulty = request.form.get('user_ai_difficulty')
            if user_id and name and dob and ai_difficulty:
                # Validate DOB is not empty
                if not dob or dob.strip() == '':
                    return redirect(url_for('parent.parent', user_id=selected_user_id, error='Date of birth is required'))
                
                user = User.query.get(user_id)
                if user:
                    user.name = name
                    user.dob = dob
                    # Ensure AI difficulty is between 1-20, default to 10
                    difficulty = int(ai_difficulty) if ai_difficulty else 10
                    user.ai_difficulty = max(1, min(20, difficulty))
                    db.session.commit()
                    return redirect(url_for('parent.parent', user_id=selected_user_id))
        
        elif action == 'add_user':
            name = request.form.get('user_name')
            dob = request.form.get('user_dob')
            ai_difficulty = request.form.get('user_ai_difficulty')
            if name and dob:
                # Validate DOB is not empty
                if not dob or dob.strip() == '':
                    return redirect(url_for('parent.parent', user_id=selected_user_id, error='Date of birth is required'))
                
                # Default AI difficulty to 10 if not provided
                difficulty = int(ai_difficulty) if ai_difficulty else 10
                # Ensure AI difficulty is between 1-20
                difficulty = max(1, min(20, difficulty))
                new_user = User(name=name, dob=dob, ai_difficulty=difficulty, parent_id=parent_obj.id)
                db.session.add(new_user)
                db.session.commit()
                return redirect(url_for('parent.parent', user_id=selected_user_id))
            else:
                # If name or dob is missing, redirect with error
                error_msg = 'Name and date of birth are required'
                return redirect(url_for('parent.parent', user_id=selected_user_id, error=error_msg))
        
        elif action == 'copy_tasks':
            target_user_id = request.form.get('target_user_id')
            source_user_id = request.form.get('source_user_id')
            
            if target_user_id and source_user_id and target_user_id != source_user_id:
                # Get tasks from source user
                source_tasks = Task.query.filter_by(user_id=source_user_id).all()
                
                # Get existing tasks for target user to avoid duplicates
                existing_tasks = Task.query.filter_by(user_id=target_user_id).all()
                existing_task_names = {task.task for task in existing_tasks}
                
                # Copy tasks that don't already exist
                for task in source_tasks:
                    if task.task not in existing_task_names:
                        new_task = Task(
                            user_id=target_user_id,
                            task=task.task,
                            frequency=task.frequency,
                            duration=task.duration,
                            log_completed_page_numbers=task.log_completed_page_numbers
                        )
                        db.session.add(new_task)
                
                db.session.commit()
                return redirect(url_for('parent.parent', user_id=target_user_id))

        return redirect(url_for('parent.parent', user_id=user_id))

    return render_template(
        'parent.html',
        users=users,
        selected_user=selected_user,
        user_tasks=user_tasks,
        error_message=error_message
    )
