from database import db
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))

    # --- New Profile Fields ---
    height = db.Column(db.Float)  # in cm
    weight = db.Column(db.Float)  # in kg
    age = db.Column(db.Integer)
    goal = db.Column(db.String(50))  # fat_loss / muscle_gain / maintain
    activity_level = db.Column(db.String(50))  # low / moderate / high


class WorkoutSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    exercise = db.Column(db.String(50))
    reps = db.Column(db.Integer)
    avg_score = db.Column(db.Float)
    calories = db.Column(db.Float)
    date = db.Column(db.DateTime, default=datetime.utcnow)


class HabitRisk(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    risk_score = db.Column(db.Float)
    date = db.Column(db.DateTime, default=datetime.utcnow)


class DietPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    calories = db.Column(db.Integer)
    protein = db.Column(db.Integer)
    carbs = db.Column(db.Integer)
    fat = db.Column(db.Integer)
    date_updated = db.Column(db.DateTime, default=datetime.utcnow)