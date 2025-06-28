from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime
import csv
import os
from openai_helper import fetch_ai_problems, get_user_difficulty, update_user_difficulty

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for session

DATA_PATH = os.path.join(os.path.dirname(__file__), 'data', 'tasks.csv')
LOG_PATH = os.path.join(os.path.dirname(__file__), 'data', 'task_log.csv')

def load_tasks_for_user(user):
    """
    Loads tasks for a specific user and updates their statuses based on the log file for the current date.
    Parameters:
        user (str): The name of the user (e.g., "Noah").
    Returns:
        list: A list of tasks with their statuses and completion times.
    """
    tasks = []
    today = datetime.now().strftime("%Y-%m-%d")  # Get today's date

    # Load tasks from the main tasks file
    with open(DATA_PATH, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row['user'] == user:
                tasks.append({"task": row['task'], "status": "TODO", "frequency": row['frequency'], "time": None})

    # Load saved statuses from the log file for the current date
    if os.path.isfile(LOG_PATH):
        with open(LOG_PATH, newline='', encoding='utf-8') as logfile:
            reader = csv.DictReader(logfile)
            for row in reader:
                if row['user'] == user and row['date'] == today:  # Match user and today's date
                    for task in tasks:
                        if task['task'] == row['task']:
                            task['status'] = row['status']
                            task['time'] = row['time'] if row['status'] == 'Done' else None

    return tasks

def log_task_status(user, task, status):
    """
    Logs the status of a task for a specific user in the task log file.
    Parameters:
        user (str): The name of the user (e.g., "Noah").
        task (str): The name of the task (e.g., "AI Problems").
        status (str): The new status of the task (e.g., "Done" or "TODO").
    """
    today = datetime.now().strftime("%Y-%m-%d")
    updated = False

    # Read the existing log entries
    if os.path.isfile(LOG_PATH):
        with open(LOG_PATH, 'r', newline='', encoding='utf-8') as logfile:
            log_rows = list(csv.DictReader(logfile))

        # Update the status for the matching task and date
        for row in log_rows:
            if row['user'] == user and row['task'] == task and row['date'] == today:
                row['status'] = status
                row['time'] = datetime.now().strftime("%H:%M:%S") if status == 'Done' else ''
                updated = True

    # If no matching entry was found, add a new one
    if not updated:
        log_rows.append({
            'user': user,
            'date': today,
            'task': task,
            'status': status,
            'time': datetime.now().strftime("%H:%M:%S") if status == 'Done' else ''
        })

    # Write the updated log back to the file
    with open(LOG_PATH, 'w', newline='', encoding='utf-8') as logfile:
        fieldnames = ['user', 'date', 'task', 'status', 'time']
        writer = csv.DictWriter(logfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(log_rows)

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        user = request.form.get('user')
        if user:
            session['user'] = user
            session['tasks'] = load_tasks_for_user(user)
            return redirect(url_for('tasks'))
    return render_template('index.html')

@app.route('/tasks', methods=['GET', 'POST'])
def tasks():
    if 'user' not in session:
        return redirect(url_for('home'))
    
    user = session['user']
    tasks = load_tasks_for_user(user)  # Load tasks and statuses for the current date

    if request.method == 'POST':
        # Handle "Mark Done" and "Unmark Done" actions
        if request.form.get('action') == 'mark':
            task_idx = int(request.form.get('task_idx'))
            task_to_mark = tasks[task_idx]
            log_task_status(user, task_to_mark['task'], 'Done')
            tasks = load_tasks_for_user(user)  # Reload tasks to reflect the updated status
        elif request.form.get('action') == 'unmark':
            task_idx = int(request.form.get('task_idx'))
            task_to_unmark = tasks[task_idx]
            log_task_status(user, task_to_unmark['task'], 'TODO')
            tasks = load_tasks_for_user(user)  # Reload tasks to reflect the updated status

    # Check if all tasks are marked as "Done"
    all_done = all(task['status'] == 'Done' for task in tasks)

    # Check if all tasks are completed before noon
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
            print(f"Error checking completion times: {e}")
            all_done_before_noon = False

    # Fetch AI problems
    ai_problems = fetch_ai_problems(num_questions=3, user=user, difficulty=get_user_difficulty(user))

    today = datetime.now().strftime("%A, %B %d, %Y")
    return render_template(
        'tasks.html',
        user=user,
        tasks=tasks,
        today=today,
        ai_problems=ai_problems,
        difficulty=get_user_difficulty(user),
        all_done=all_done,  # Pass the flag for all tasks done
        all_done_before_noon=all_done_before_noon  # Pass the flag for all tasks done before noon
    )

@app.route('/history')
def history():
    if 'user' not in session:
        return redirect(url_for('home'))
    user = session['user']
    history_data = []
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row['user'] == user:
                    history_data.append(row)
    
    # Group by date, ordered by date desc
    from collections import defaultdict
    grouped = defaultdict(list)
    for row in history_data:
        grouped[row['date']].append(row)
    sorted_dates = sorted(grouped.keys(), reverse=True)

    # Calculate star status for each date
    date_stars = {}
    for date, tasks in grouped.items():
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
        user=user,
        grouped=grouped,
        sorted_dates=sorted_dates,
        date_stars=date_stars
    )

@app.route('/parent', methods=['GET', 'POST'])
def parent():
    # Load all users and their tasks
    users = set()
    user_tasks = {}
    with open(DATA_PATH, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            users.add(row['user'])
            user_tasks.setdefault(row['user'], []).append({'task': row['task'], 'frequency': row['frequency']})

    selected_user = request.form.get('selected_user') if request.method == 'POST' else None

    # Handle add/edit/delete actions
    message = ""
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            user = request.form['user']
            task = request.form['task']
            frequency = request.form['frequency']
            # Append new task
            with open(DATA_PATH, 'a', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([user, task, frequency])
            message = f"Added task '{task}' for {user}."
        elif action == 'delete':
            user = request.form['user']
            task = request.form['task']
            # Remove task
            rows = []
            with open(DATA_PATH, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    if not (row['user'] == user and row['task'] == task):
                        rows.append(row)
            with open(DATA_PATH, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['user', 'task', 'frequency']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            message = f"Deleted task '{task}' for {user}."
        elif action == 'edit':
            user = request.form['user']
            old_task = request.form['old_task']
            new_task = request.form['new_task']
            frequency = request.form['frequency']
            # Edit task
            rows = []
            with open(DATA_PATH, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    if row['user'] == user and row['task'] == old_task:
                        row['task'] = new_task
                        row['frequency'] = frequency
                    rows.append(row)
            with open(DATA_PATH, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['user', 'task', 'frequency']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            message = f"Edited task '{old_task}' for {user}."
        # Reload user_tasks after changes
        user_tasks = {}
        with open(DATA_PATH, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                user_tasks.setdefault(row['user'], []).append({'task': row['task'], 'frequency': row['frequency']})

    return render_template('parent.html', users=sorted(users), user_tasks=user_tasks, selected_user=selected_user, message=message)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)