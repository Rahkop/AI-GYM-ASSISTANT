import numpy as np
from sklearn.ensemble import RandomForestClassifier
import joblib

def train_model():
    X = np.array([
        [5, 0, 7, 85],
        [2, 3, 1, 60],
        [6, 0, 10, 90],
        [1, 4, 0, 50],
    ])
    y = np.array([0, 1, 0, 1])

    model = RandomForestClassifier()
    model.fit(X, y)
    joblib.dump(model, "habit_model.pkl")

def predict_risk(workouts, missed, streak, avg_score):
    model = joblib.load("habit_model.pkl")
    return model.predict([[workouts, missed, streak, avg_score]])[0]