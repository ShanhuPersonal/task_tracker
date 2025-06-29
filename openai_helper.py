import openai
from config import OPENAI_API_KEY
import csv
import os
import json
from datetime import datetime
from models import User, db  # Import User model and db session

# Initialize the OpenAI client
client = openai.OpenAI(api_key=OPENAI_API_KEY)

problem_generation_prompt = """
You are a creative educational assistant tasked with generating engaging, witty, and diverse math, logic, or science questions for kids. The difficulty levels should range from 0 to 20. As of June 2025, Dylan is 8 years old, about to enter 3rd grade. Noah is 10 years old, about to enter 5th grade. Avoid repeating questions from prior sets and aim for variety inspired by examples from around the world. Each question should be phrased clearly and encourage thoughtful problem solving.

Generate {} questions for {} with difficulty {}. Format the output as an HTML unordered list (<ul>) where each question is wrapped in a <li> tag. Ensure the HTML is valid and properly structured.

Only return the list. Do not include any additional text or explanations.

To avoid repeating questions, ensure that the generated problems are unique and not similar to those previously generated. You can draw inspiration from various educational resources and examples from around the world. 
"""

QUESTIONS_LOG_FILE = os.path.join(os.path.dirname(__file__), 'data', 'questions_log.json')

def get_user_difficulty(user_name):
    """
    Reads the difficulty level for a specific user from the database.
    Parameters:
        user_name (str): Name of the user (e.g., "Dylan" or "Noah").
    Returns:
        int: The difficulty level for the user.
    """
    user = User.query.filter_by(name=user_name).first()
    if user:
        return user.ai_difficulty
    return 10  # Default difficulty if not found

def fetch_ai_problems(num_questions=3, user="Dylan", difficulty=12, force_refresh=False):
    """
    Fetches AI problems from OpenAI's API using the GPT-4o engine synchronously.
    If questions for the same user, difficulty, and date already exist in the log, use the most recent one unless force_refresh is True.
    Parameters:
        num_questions (int): Number of questions to generate.
        user (str): Name of the user (e.g., "Dylan" or "Noah").
        difficulty (int): Difficulty level of the questions (0-20).
        force_refresh (bool): If True, bypass the cache and call OpenAI directly.
    Returns:
        str: HTML string of generated problems or an error message if the API call fails.
    """
    try:
        # Check if questions for the same user, difficulty, and date already exist
        today = datetime.now().strftime("%Y-%m-%d")
        if not force_refresh and os.path.exists(QUESTIONS_LOG_FILE):
            with open(QUESTIONS_LOG_FILE, 'r', encoding='utf-8') as json_file:
                data = json.load(json_file)
                # Filter entries for the same user, difficulty, and date
                filtered_entries = [
                    entry for entry in data
                    if entry['user'] == user and entry['difficulty'] == difficulty and entry['timestamp'].startswith(today)
                ]
                # Sort by timestamp in descending order to get the most recent entry
                if filtered_entries:
                    most_recent_entry = sorted(filtered_entries, key=lambda x: x['timestamp'], reverse=True)[0]
                    print(f"Using most recent cached questions for {user} at difficulty {difficulty} from {today}")
                    return most_recent_entry['questions']

        # If no cached questions exist or force_refresh is True, call OpenAI API
        prompt = problem_generation_prompt.format(num_questions, user, difficulty)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful and creative educational assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        # Access the content of the first choice
        problems_html = response.choices[0].message.content.strip()

        # Remove Markdown code block markers if present
        if problems_html.startswith("```html"):
            problems_html = problems_html[7:]  # Remove the opening ```html
        if problems_html.endswith("```"):
            problems_html = problems_html[:-3]  # Remove the closing ```

        # Save the problems to the JSON log
        save_questions_to_json(user, difficulty, problems_html)

        return problems_html
    except Exception as e:
        print(f"Error fetching AI problems: {e}")
        return "<p>Error fetching AI problems. Please try again later.</p>"

def save_questions_to_json(user, difficulty, problems_html):
    """
    Saves the fetched questions to a JSON file with metadata.
    Parameters:
        user (str): Name of the user (e.g., "Dylan" or "Noah").
        difficulty (int): Difficulty level of the questions.
        problems_html (str): HTML string of generated questions.
    """
    try:
        # Prepare the data to save
        entry = {
            "user": user,
            "difficulty": difficulty,
            "questions": problems_html,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        # Load existing data from the JSON file
        if os.path.exists(QUESTIONS_LOG_FILE):
            with open(QUESTIONS_LOG_FILE, 'r', encoding='utf-8') as json_file:
                data = json.load(json_file)
        else:
            data = []

        # Append the new entry
        data.append(entry)

        # Save the updated data back to the JSON file
        with open(QUESTIONS_LOG_FILE, 'w', encoding='utf-8') as json_file:
            json.dump(data, json_file, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving questions to JSON file: {e}")

def update_user_difficulty(user_name, new_difficulty):
    """
    Updates the difficulty level for a specific user in the database.
    Parameters:
        user_name (str): Name of the user (e.g., "Dylan" or "Noah").
        new_difficulty (int): The new difficulty level to set.
    """
    user = User.query.filter_by(name=user_name).first()
    if user:
        user.ai_difficulty = new_difficulty
        db.session.commit()