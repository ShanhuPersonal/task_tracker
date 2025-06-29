from flask import Blueprint, render_template, request, redirect, url_for, session
from models import User

bp = Blueprint('home', __name__)

@bp.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        selected_user_id = request.form.get('selected_user_id')
        if selected_user_id:
            session['user_id'] = int(selected_user_id)
            user = User.query.get(int(selected_user_id))
            if user:
                session['user'] = user.name
            return redirect(url_for('tasks.tasks'))
    return render_template('index.html')
