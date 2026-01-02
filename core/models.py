from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    projects = db.relationship(
        "Project",
        backref="user",
        lazy=True,
        cascade="all, delete-orphan"
    )

    logs = db.relationship(
        "Log",
        backref="user",
        lazy=True,
        cascade="all, delete-orphan"
    )


class Project(db.Model):
    __tablename__ = "project"

    id = db.Column(db.Integer, primary_key=True)

    # ✅ THIS IS THE MAIN FIX
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    name = db.Column(db.String(100), nullable=False)
    path = db.Column(db.String(300))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Log(db.Model):
    __tablename__ = "log"

    id = db.Column(db.Integer, primary_key=True)

    # ✅ SAME FIX HERE
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    message = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
