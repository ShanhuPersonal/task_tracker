from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from openai_helper import fetch_ai_problems, get_user_difficulty, update_user_difficulty, get_hint_from_cache
from datetime import date
from models import User
from timezone_utils import now_pst, format_pst_date

ai_problems_bp = Blueprint('ai_problems', __name__, url_prefix='/ai_problems')

@ai_problems_bp.route('/')
def ai_problems():
    # Fetch AI problems and user difficulty
    user = request.args.get('user') or session.get('user', 'Guest')  # Check query parameters first, then session
    today = now_pst().strftime('%B %d, %Y')

    try:
        difficulty = get_user_difficulty(user)
        problems_data = fetch_ai_problems(3, user, difficulty)
        # Extract the HTML for backward compatibility with template
        problems = problems_data.get('questions_html', '<ul><li>Error loading problems</li></ul>')
    except Exception as e:
        difficulty = 10  # Default to 10 instead of None
        problems = '<ul><li>Error loading problems</li></ul>'
        # Could add proper logging here if needed
        # print(f"Error fetching AI problems or difficulty: {e}")

    return render_template('ai_problems.html', ai_problems=problems, difficulty=difficulty, user=user, today=today)

@ai_problems_bp.route('/get_hint', methods=['POST'])
def get_hint():
    question_id = int(request.form.get('question_id')) - 1  # Convert to zero-based index
    user_name = request.args.get('user') or session.get('user', 'default_user')

    # Fetch user and validate
    user = User.query.filter_by(name=user_name).first()
    if not user:
        flash("User not found! Please select a valid user.", "error")
        return redirect(url_for('ai_problems.ai_problems'))

    # Get difficulty and retrieve hint from cache
    difficulty = get_user_difficulty(user_name)
    hint_data = get_hint_from_cache(user_name, difficulty, question_id)
    
    if hint_data:
        hint = hint_data['hint']
        question = hint_data['question']
    else:
        flash("Hint not available! Please refresh the questions and try again.", "error")
        hint = "Sorry, hint not available right now. Try refreshing the page!"
        question = "Question not found"

    # Fetch AI problems again to pass to the template
    problems_data = fetch_ai_problems(3, user_name, difficulty)
    ai_problems = problems_data.get('questions_html', '<ul><li>Error loading problems</li></ul>')

    # Return the hint along with AI problems
    return render_template('ai_problems.html', hint=hint, question=question, user=user_name, ai_problems=ai_problems, difficulty=difficulty, today=date.today().strftime('%B %d, %Y'))

@ai_problems_bp.route('/refresh', methods=['POST'])
def refresh_questions():
    user = request.form.get('user', 'default_user')  # Replace with actual user logic
    difficulty = get_user_difficulty(user)
    fetch_ai_problems(3, user, difficulty, force_refresh=True)
    return redirect(url_for('ai_problems.ai_problems', user=user))

@ai_problems_bp.route('/difficulty', methods=['POST'])
def change_difficulty():
    user = request.form.get('user', 'default_user')  # Fetch user from form data
    action = request.form.get('difficulty_action')
    user_obj = User.query.filter_by(name=user).first()

    if user_obj:
        current_difficulty = user_obj.ai_difficulty if user_obj.ai_difficulty is not None else 10
        if action == 'increase':
            if current_difficulty >= 20:
                flash("Max difficulty is 20, dude!", "warning")
                new_difficulty = current_difficulty
            else:
                new_difficulty = current_difficulty + 1
        elif action == 'decrease':
            new_difficulty = max(1, current_difficulty - 1)
        else:
            new_difficulty = current_difficulty

        update_user_difficulty(user, new_difficulty)

    return redirect(url_for('ai_problems.ai_problems', user=user))
