from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from models import User, Task, TaskLog
from openai_helper import fetch_ai_problems, get_user_difficulty, update_user_difficulty
from datetime import datetime
from extensions import db
from timezone_utils import now_pst, format_pst_date, format_pst_time, format_pst_datetime, get_pst_weekday

bp = Blueprint('tasks', __name__)

def load_tasks_for_user(user_id):
    """
    Loads tasks for a specific user and updates their statuses based on the log file for the current date.
    Parameters:
        user_id (int): The ID of the user.
    Returns:
        list: A list of tasks with their statuses and completion times.
    """
    today = now_pst()
    today_str = format_pst_date(today)
    today_weekday = get_pst_weekday(today)  # Get the current weekday (e.g., Mon, Tue)

    tasks = Task.query.filter_by(user_id=user_id).all()
    task_logs = TaskLog.query.filter_by(user_id=user_id, date=today_str).all()

    task_list = []
    for task in tasks:
        # Check if the task should be shown today based on its frequency
        if task.frequency.lower() == "daily" or today_weekday in [day.strip().capitalize() for day in task.frequency.split(",")]:
            log = next((log for log in task_logs if log.task == task.task), None)
            task_list.append({
                "task": task.task,
                "status": log.status if log else "TODO",
                "frequency": task.frequency,
                "duration": task.duration if task.duration is not None else "as needed",  # Show 'as needed' for empty durations
                "time": log.time if log and log.status == "Done" else None,
                "log_completed_page_numbers": task.log_completed_page_numbers  # Add this field
            })
    return task_list

def log_task_status(user_id, task, status, page_numbers=None):
    """
    Logs the status of a task for a specific user in the task log table.
    Parameters:
        user_id (int): The ID of the user.
        task (str): The name of the task (e.g., "AI Problems").
        status (str): The new status of the task (e.g., "Done" or "TODO").
        page_numbers (str): The page numbers completed (optional).
    """
    today = format_pst_date()
    time = format_pst_time() if status == "Done" else None

    log = TaskLog.query.filter_by(user_id=user_id, task=task, date=today).first()
    if log:
        log.status = status
        log.time = time
        if page_numbers is not None:
            log.completed_page_numbers = page_numbers
    else:
        log = TaskLog(user_id=user_id, task=task, date=today, status=status, time=time, completed_page_numbers=page_numbers)
        db.session.add(log)
    db.session.commit()

def check_all_done_before_noon(tasks):
    """
    Checks if all tasks are completed before noon.
    Parameters:
        tasks (list): A list of tasks with their statuses and completion times.
    Returns:
        bool: True if all tasks are completed before noon, False otherwise.
    """
    try:
        times = [task['time'] for task in tasks if task['time']]
        if times:
            latest_time = max(datetime.strptime(time, "%H:%M:%S") for time in times)
            return latest_time.hour < 12
    except Exception as e:
        print(f"Error checking completion times: {e}")
    return False

@bp.route('/tasks', methods=['GET', 'POST'])
def tasks():
    if 'user_id' not in session:
        return redirect(url_for('home.home'))

    user_id = session['user_id']
    user = User.query.get(user_id)
    if not user:
        return redirect(url_for('home.home'))

    tasks = load_tasks_for_user(user_id)

    # Initialize difficulty before handling POST requests
    difficulty = get_user_difficulty(user.name)

    if request.method == 'POST':
        action = request.form.get('action')
        task_idx = request.form.get('task_idx')
        if task_idx is not None:
            task_idx = int(task_idx)
            task_to_update = tasks[task_idx]
            if action == 'mark':
                # Check if this task requires page numbers
                if task_to_update['log_completed_page_numbers']:
                    # For tasks that need page numbers, we'll handle this via JavaScript
                    # The form submission will be intercepted by JavaScript
                    pass
                else:
                    # For normal tasks, mark as done immediately
                    log_task_status(user_id, task_to_update['task'], 'Done')
            elif action == 'unmark':
                log_task_status(user_id, task_to_update['task'], 'TODO')
            tasks = load_tasks_for_user(user_id)

        difficulty_action = request.form.get('difficulty_action')
        refresh_questions = request.form.get('refresh_questions')

        if difficulty_action:
            if difficulty_action == 'increase':
                if difficulty >= 20:
                    flash("Already at max level, dude!", "warning")
                else:
                    print(f"Current difficulty before increase: {difficulty}")
                    new_difficulty = min(difficulty + 1, 20)  # Updated max difficulty to 20
                    update_user_difficulty(user.name, new_difficulty)
                    print(f"New difficulty after increase: {new_difficulty}")
            elif difficulty_action == 'decrease':
                print(f"Current difficulty before decrease: {difficulty}")
                new_difficulty = max(difficulty - 1, 1)  # Assuming min difficulty is 1
                update_user_difficulty(user.name, new_difficulty)
                print(f"New difficulty after decrease: {new_difficulty}")

            # Refresh difficulty after update
            difficulty = get_user_difficulty(user.name)

        # Handle refresh questions
        force_refresh = refresh_questions == 'true' if refresh_questions else False
    else:
        force_refresh = False

    all_done = all(task['status'] == 'Done' for task in tasks)
    all_done_before_noon = check_all_done_before_noon(tasks)

    today = format_pst_datetime()

    return render_template(
        'tasks.html',
        user=user.name,
        tasks=tasks,
        today=today,
    )

@bp.route('/submit_page_numbers', methods=['POST'])
def submit_page_numbers():
    """Handle page numbers submission via AJAX"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    user_id = session['user_id']
    task_name = request.json.get('task_name')
    page_numbers = request.json.get('page_numbers', '').strip()
    
    if not task_name:
        return jsonify({'success': False, 'error': 'Task name is required'}), 400
    
    # Log the task as done with page numbers
    log_task_status(user_id, task_name, 'Done', page_numbers)
    
    return jsonify({'success': True})
