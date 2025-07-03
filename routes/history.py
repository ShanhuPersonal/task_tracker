from flask import Blueprint, render_template, session, redirect, url_for
from models import TaskLog, User, Task
from datetime import datetime
from collections import defaultdict
from timezone_utils import get_pst_weekday

bp = Blueprint('history', __name__)

@bp.route('/history')
def history():
    if 'user_id' not in session:
        return redirect(url_for('home.home'))

    user_id = session['user_id']
    user = User.query.get(user_id)
    if not user:
        return redirect(url_for('home.home'))

    # Query task logs for the user
    task_logs = TaskLog.query.filter_by(user_id=user_id).all()

    # Fetch all tasks for the user from the database
    all_tasks = Task.query.filter_by(user_id=user.id).all()

    # Group by date, ordered by date desc
    grouped = defaultdict(list)
    
    # Create a lookup for task details
    task_details = {task.task: {'frequency': task.frequency, 'duration': task.duration} for task in all_tasks}
    
    for log in task_logs:
        task_info = task_details.get(log.task, {'frequency': 'Unknown', 'duration': None})
        grouped[log.date].append({
            "task": log.task,
            "status": log.status,
            "time": log.time,
            "completed_page_numbers": log.completed_page_numbers,
            "frequency": task_info['frequency'],
            "duration": task_info['duration']
        })
    sorted_dates = sorted(grouped.keys(), reverse=True)

    # Calculate star status for each date
    date_stars = {}
    # Filter tasks based on frequency for each date
    today_weekday = get_pst_weekday()
    for date, tasks in grouped.items():
        tasks_with_status = {task['task']: task for task in tasks}
        for task in all_tasks:
            # Check if the task should be shown on this date based on its frequency
            if task.frequency.lower() == "daily" or today_weekday in [day.strip().capitalize() for day in task.frequency.split(",")]:
                if task.task not in tasks_with_status:
                    tasks.append({
                        "task": task.task, 
                        "status": "TODO", 
                        "time": None, 
                        "completed_page_numbers": None,
                        "frequency": task.frequency,
                        "duration": task.duration
                    })

        all_done = all(task['status'] == 'Done' for task in tasks)
        all_done_before_noon = False
        if all_done:
            try:
                # Extract times and check if all are before noon
                times = [task['time'] for task in tasks if task['time']]
                if times:
                    latest_time = max(datetime.strptime(time, "%H:%M:%S") for time in times)
                    if latest_time.hour < 12:  # Check if the latest time is before noon
                        all_done_before_noon = True
            except Exception as e:
                print(f"Error calculating stars for date {date}: {e}")
                all_done_before_noon = False
        date_stars[date] = 2 if all_done_before_noon else (1 if all_done else 0)

    return render_template(
        'history.html',
        user=user.name,
        grouped=grouped,
        sorted_dates=sorted_dates,
        date_stars=date_stars
    )
