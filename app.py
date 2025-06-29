from flask import Flask
from flask_migrate import Migrate
from extensions import db
from routes import home, tasks, history, parent
from routes.ai_problems import ai_problems_bp

migrate = Migrate(db)

def create_app():
    app = Flask(__name__)
    app.secret_key = 'your_secret_key'

    # SQLite database configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///task_tracker.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints
    app.register_blueprint(home)
    app.register_blueprint(tasks)
    app.register_blueprint(history)
    app.register_blueprint(parent)
    app.register_blueprint(ai_problems_bp)

    with app.app_context():
        db.create_all()  # Create tables if they don't exist

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)