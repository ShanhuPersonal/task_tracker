# Task Tracker Flask Application

This is a simple Flask application called "task_tracker" that allows users to select a name from a dropdown menu and confirm their selection.

## Project Structure

```
task_tracker
├── app.py
├── templates
│   └── index.html
├── static
│   └── style.css
└── README.md
```

## Setup Instructions

1. **Clone the repository**:
   ```
   git clone <repository-url>
   cd task_tracker
   ```

2. **Create a virtual environment**:
   ```
   python -m venv venv
   ```

3. **Activate the virtual environment**:
   - On Windows:
     ```
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```
     source venv/bin/activate
     ```

4. **Install the required packages**:
   ```
   pip install Flask
   ```

5. **Run the application**:
   ```
   python app.py
   ```

6. **Open your web browser** and go to `http://127.0.0.1:5000` to view the application.

## Overview

The application features a home page with a dropdown menu that allows users to select either "Noah" or "Dylan." After making a selection, users can click the confirm button to submit their choice. The application is styled using a separate CSS file located in the `static` directory.