from flask import Flask
from core.models import db
from core.auth import auth

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "change-this-secret-key"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///../instance/app.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    app.register_blueprint(auth)

    from app.routes import main
    app.register_blueprint(main)

    with app.app_context():
        db.create_all()

    return app
