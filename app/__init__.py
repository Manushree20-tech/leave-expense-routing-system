import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from pathlib import Path

db = SQLAlchemy()

def create_app(test_config=None):
    load_dotenv()
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "development-only-change-me")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///leave_expense_routing.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024
    if test_config:
        app.config.update(test_config)
    db.init_app(app)
    from . import models
    from .routes import bp
    app.register_blueprint(bp)
    with app.app_context():
        db.create_all()
        from .seed import seed_reference_data
        seed_reference_data()
    return app
