from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime
import csv
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for session

DATA_PATH = os.path.join(os.path.dirname(__file__), 'data', 'tasks.csv')
LOG_PATH = os.path.join(os.path.dirname(__file__), 'data', 'task_log.csv')

def load_tasks_for_user(user):
    tasks = []
    with open(DATA_PATH, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row['user'] == user:
                tasks.append({"task": row['task'], "status": "TODO", "frequency": row['frequency']})
    return tasks

def log_task_status(user, task, status):
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")
    log_rows = []

    # Read all existing log rows except the one to update
    if os.path.isfile(LOG_PATH):
        with open(LOG_PATH, newline='', encoding='utf-8') as logfile:
            reader = csv.DictReader(logfile)
            for row in reader:
                # Keep all rows except the one for this user, date, and task
                if not (row['user'] == user and row['date'] == date_str and row['task'] == task):
                    log_rows.append(row)

    # Add the updated/new row
    log_rows.append({
        'user': user,
        'date': date_str,
        'task': task,
        'status': status,
        'time': time_str
    })

    # Write all rows back to the CSV
    with open(LOG_PATH, 'w', newline='', encoding='utf-8') as logfile:
        fieldnames = ['user', 'date', 'task', 'status', 'time']
        writer = csv.DictWriter(logfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in log_rows:
            writer.writerow(row)

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
    tasks = session.get('tasks', [])
    if request.method == 'POST':
        idx = int(request.form.get('task_idx'))
        action = request.form.get('action')
        now = datetime.now()
        time_str = now.strftime("%H:%M:%S")
        if action == 'mark':
            tasks[idx]['status'] = 'Done'
            tasks[idx]['time'] = time_str  # Add time of completion
            log_task_status(session['user'], tasks[idx]['task'], 'Done')
        elif action == 'unmark':
            tasks[idx]['status'] = 'TODO'
            tasks[idx]['time'] = None
            log_task_status(session['user'], tasks[idx]['task'], 'TODO')
        session['tasks'] = tasks
    # Ensure each task has a 'time' key for display
    for t in tasks:
        if 'time' not in t:
            t['time'] = None
    today = datetime.now().strftime("%A, %B %d, %Y")
    return render_template('tasks.html', user=session['user'], tasks=tasks, today=today)

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
    from operator import itemgetter
    grouped = defaultdict(list)
    for row in history_data:
        grouped[row['date']].append(row)
    sorted_dates = sorted(grouped.keys(), reverse=True)
    return render_template('history.html', user=user, grouped=grouped, sorted_dates=sorted_dates)

if __name__ == '__main__':
    app.run(debug=True)