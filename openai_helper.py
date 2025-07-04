import openai
from config import OPENAI_API_KEY
import os
import json
from datetime import datetime
from models import User, db  # Import User model and db session
from timezone_utils import format_pst_date, now_pst

# Initialize the OpenAI client
client = openai.OpenAI(api_key=OPENAI_API_KEY)

problem_generation_prompt = """
You are a creative educational assistant tasked with generating engaging, witty, and diverse math, logic, or science questions for kids. The difficulty levels should range from 0 to 20. 

Generate {} questions for {} (age {}) with difficulty {}. For each question, also provide a helpful hint that gives guidance without giving away the answer. The hint should be age-appropriate and encouraging.

You MUST return your response as a valid JSON object with the following exact structure:

{{
  "questions_html": "<ul><li>First question here</li><li>Second question here</li><li>Third question here</li></ul>",
  "questions_and_hints": [
    {{
      "question": "First question here",
      "hint": "A helpful hint for the first question"
    }},
    {{
      "question": "Second question here", 
      "hint": "A helpful hint for the second question"
    }},
    {{
      "question": "Third question here",
      "hint": "A helpful hint for the third question"
    }}
  ]
}}

IMPORTANT:
- Return ONLY the JSON object, no additional text
- Ensure the HTML in questions_html is valid and properly formatted
- The questions in questions_html and questions_and_hints arrays must match exactly
- Each hint should be brief, encouraging, and age-appropriate for a {}-year-old child
- Avoid repeating questions from previous sets
- Make sure the questions are appropriate for the child's age level

To avoid repeating questions, ensure that the generated problems are unique and not similar to those previously generated. You can draw inspiration from various educational resources and examples from around the world.
"""

QUESTIONS_LOG_FILE = os.path.join(os.path.dirname(__file__), 'data', 'questions_log.json')

def calculate_age(dob_string):
    """
    Calculate the age from date of birth string.
    Parameters:
        dob_string (str): Date of birth in format "YYYY-MM-DD".
    Returns:
        int: Age in years, or None if dob_string is invalid.
    """
    try:
        if not dob_string:
            return None
        dob = datetime.strptime(dob_string, "%Y-%m-%d")
        today = datetime.now()
        age = today.year - dob.year
        # Adjust if birthday hasn't occurred this year
        if today.month < dob.month or (today.month == dob.month and today.day < dob.day):
            age -= 1
        return age
    except ValueError:
        print(f"Invalid date format for DOB: {dob_string}")
        return None

def get_user_difficulty(user_name):
    """
    Reads the difficulty level for a specific user from the database.
    Parameters:
        user_name (str): Name of the user (e.g., "Dylan" or "Noah").
    Returns:
        int: The difficulty level for the user (1-20, default 10).
    """
    user = User.query.filter_by(name=user_name).first()
    if user and user.ai_difficulty is not None:
        # Ensure the difficulty is within valid range
        return max(1, min(20, user.ai_difficulty))
    return 10  # Default difficulty if user not found or ai_difficulty is None

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
        dict: Dictionary with 'questions_html' and 'questions_and_hints' keys, or error structure if API call fails.
    """
    try:
        # Get user's age from database
        user_obj = User.query.filter_by(name=user).first()
        user_age = None
        if user_obj and user_obj.dob:
            user_age = calculate_age(user_obj.dob)
        
        # Default age if not found or invalid
        if user_age is None:
            user_age = 8  # Default age if DOB is not available
            print(f"Warning: Could not calculate age for user {user}, using default age {user_age}")

        # Check if questions for the same user, difficulty, and date already exist
        today = format_pst_date()
        if not force_refresh and os.path.exists(QUESTIONS_LOG_FILE):
            with open(QUESTIONS_LOG_FILE, 'r', encoding='utf-8') as json_file:
                data = json.load(json_file)
                # Filter entries for the same user, difficulty, and date
                # Only look for entries with the new format (has 'questions_and_hints')
                filtered_entries = [
                    entry for entry in data
                    if (entry['user'] == user and entry['difficulty'] == difficulty and 
                        entry['timestamp'].startswith(today) and 'questions_and_hints' in entry)
                ]
                # Sort by timestamp in descending order to get the most recent entry
                if filtered_entries:
                    most_recent_entry = sorted(filtered_entries, key=lambda x: x['timestamp'], reverse=True)[0]
                    print(f"Using most recent cached questions for {user} (age {user_age}) at difficulty {difficulty} from {today}")
                    return {
                        'questions_html': most_recent_entry['questions_html'],
                        'questions_and_hints': most_recent_entry['questions_and_hints']
                    }

        # If no cached questions exist or force_refresh is True, call OpenAI API
        prompt = problem_generation_prompt.format(num_questions, user, user_age, difficulty, user_age)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful and creative educational assistant. You must respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        # Access the content of the first choice
        response_content = response.choices[0].message.content.strip()

        # Remove Markdown code block markers if present
        if response_content.startswith("```json"):
            response_content = response_content[7:]  # Remove the opening ```json
        elif response_content.startswith("```"):
            response_content = response_content[3:]  # Remove the opening ```
        if response_content.endswith("```"):
            response_content = response_content[:-3]  # Remove the closing ```

        # Parse the JSON response
        try:
            problems_data = json.loads(response_content)
            
            # Validate the expected structure
            if not isinstance(problems_data, dict) or 'questions_html' not in problems_data or 'questions_and_hints' not in problems_data:
                raise ValueError("Response does not have expected structure")
            
            if not isinstance(problems_data['questions_and_hints'], list):
                raise ValueError("questions_and_hints must be a list")
                
            # Validate each question and hint pair
            for item in problems_data['questions_and_hints']:
                if not isinstance(item, dict) or 'question' not in item or 'hint' not in item:
                    raise ValueError("Each item in questions_and_hints must have 'question' and 'hint' keys")
            
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error parsing JSON response: {e}")
            print(f"Raw response: {response_content}")
            return {
                'questions_html': "<ul><li>Error fetching AI problems. Please try again later.</li></ul>",
                'questions_and_hints': [{"question": "Error fetching problems", "hint": "Please try refreshing the page"}]
            }

        # Save the problems to the JSON log
        save_questions_to_json(user, difficulty, problems_data)

        return problems_data
    except Exception as e:
        print(f"Error fetching AI problems: {e}")
        return {
            'questions_html': "<ul><li>Error fetching AI problems. Please try again later.</li></ul>",
            'questions_and_hints': [{"question": "Error fetching problems", "hint": "Please try refreshing the page"}]
        }

def save_questions_to_json(user, difficulty, problems_data):
    """
    Saves the fetched questions and hints to a JSON file with metadata.
    Parameters:
        user (str): Name of the user (e.g., "Dylan" or "Noah").
        difficulty (int): Difficulty level of the questions.
        problems_data (dict): Dictionary containing questions_html and questions_and_hints.
    """
    try:
        # Prepare the data to save
        entry = {
            "user": user,
            "difficulty": difficulty,
            "questions_html": problems_data['questions_html'],
            "questions_and_hints": problems_data['questions_and_hints'],
            "timestamp": now_pst().strftime("%Y-%m-%d %H:%M:%S")
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
        print(f"Updating difficulty for user {user_name} from {user.ai_difficulty} to {new_difficulty}")
        user.ai_difficulty = new_difficulty
        db.session.commit()
        print(f"Difficulty updated successfully for user {user_name}")
    else:
        print(f"User {user_name} not found in the database")

def get_hint_from_cache(user, difficulty, question_index):
    """
    Retrieves a hint for a specific question from the cached data.
    Parameters:
        user (str): Name of the user (e.g., "Dylan" or "Noah").
        difficulty (int): Difficulty level of the questions.
        question_index (int): Zero-based index of the question (0, 1, or 2).
    Returns:
        dict: Dictionary with 'question' and 'hint' keys, or None if not found.
    """
    try:
        today = format_pst_date()
        if os.path.exists(QUESTIONS_LOG_FILE):
            with open(QUESTIONS_LOG_FILE, 'r', encoding='utf-8') as json_file:
                data = json.load(json_file)
                # Filter entries for the same user, difficulty, and date
                # Only look for entries with the new format (has 'questions_and_hints')
                filtered_entries = [
                    entry for entry in data
                    if (entry['user'] == user and entry['difficulty'] == difficulty and 
                        entry['timestamp'].startswith(today) and 'questions_and_hints' in entry)
                ]
                # Sort by timestamp in descending order to get the most recent entry
                if filtered_entries:
                    most_recent_entry = sorted(filtered_entries, key=lambda x: x['timestamp'], reverse=True)[0]
                    questions_and_hints = most_recent_entry['questions_and_hints']
                    if 0 <= question_index < len(questions_and_hints):
                        return questions_and_hints[question_index]
        return None
    except Exception as e:
        print(f"Error retrieving hint from cache: {e}")
        return None