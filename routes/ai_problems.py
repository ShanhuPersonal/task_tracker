from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from openai_helper import fetch_ai_problems, get_user_difficulty, update_user_difficulty
from datetime import date, datetime
from models import User
from openai import OpenAI
from config import OPENAI_API_KEY

# Initialize the OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

ai_problems_bp = Blueprint('ai_problems', __name__, url_prefix='/ai_problems')

@ai_problems_bp.route('/')
def ai_problems():
    # Fetch AI problems and user difficulty
    user = request.args.get('user') or session.get('user', 'Guest')  # Check query parameters first, then session
    today = date.today().strftime('%B %d, %Y')

    try:
        difficulty = get_user_difficulty(user)
        problems = fetch_ai_problems(3, user, difficulty)
    except Exception as e:
        difficulty = 10  # Default to 10 instead of None
        problems = []
        # Could add proper logging here if needed
        # print(f"Error fetching AI problems or difficulty: {e}")

    return render_template('ai_problems.html', ai_problems=problems, difficulty=difficulty, user=user, today=today)

@ai_problems_bp.route('/get_hint', methods=['POST'])
def get_hint():
    question_id = int(request.form.get('question_id')) - 1  # Convert to zero-based index
    user_name = request.args.get('user') or session.get('user', 'default_user')

    # Fetch user and calculate age
    user = User.query.filter_by(name=user_name).first()
    if not user:
        flash("User not found! Please select a valid user.", "error")
        return redirect(url_for('ai_problems.ai_problems'))

    if not user.dob:
        flash("User's date of birth (DOB) is missing!", "error")
        return redirect(url_for('ai_problems.ai_problems'))

    # Convert user.dob to a datetime.date object if it's a string
    if isinstance(user.dob, str):
        user.dob = datetime.strptime(user.dob, '%Y-%m-%d').date()

    age = (date.today() - user.dob).days // 365

    # Fetch the question
    questions = fetch_ai_problems(3, user_name, user.ai_difficulty).split('<li>')[1:4]
    question = questions[question_id].split('</li>')[0]

    # Call OpenAI for a hint
    hint_prompt = f"Provide a hint for the following question targeted at a {age}-year-old kid. Keep it short and brief: {question}"
    hint = ""  # Default hint
    try:
        hint = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": hint_prompt}
            ],
            temperature=0.7,
            max_tokens=500
        ).choices[0].message.content.strip()
    except Exception as e:
        # Could add proper logging here if needed
        # print(f"Error fetching hint: {e}")
        flash("Error fetching hint!", "error")

    # Fetch AI problems again to pass to the template
    ai_problems = fetch_ai_problems(3, user_name, user.ai_difficulty)

    # Return the hint along with AI problems
    return render_template('ai_problems.html', hint=hint, question=question, user=user_name, ai_problems=ai_problems, difficulty=user.ai_difficulty, today=date.today().strftime('%B %d, %Y'))

@ai_problems_bp.route('/refresh', methods=['POST'])
def refresh_questions():
    user = request.form.get('user', 'default_user')  # Replace with actual user logic
    difficulty = get_user_difficulty(user)
    fetch_ai_problems(3, user, difficulty, force_refresh=True)
    return redirect(url_for('ai_problems.ai_problems'))

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

    return redirect(url_for('ai_problems.ai_problems'))
