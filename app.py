from flask import Flask, render_template, request, redirect, send_file
from database import db
from models import User, WorkoutSession, HabitRisk, DietPlan
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from habit_model import predict_risk
from diet_engine import calculate_diet
from chat_engine import generate_response
from datetime import datetime
try:
    from pose_analyzer import analyze_workout
except:
    analyze_workout = None

import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter


app = Flask(__name__)
app.secret_key = "supersecretkey"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///fitness.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


with app.app_context():
    db.create_all()


# -----------------------
# HOME
# -----------------------
@app.route("/")
def home():
    return render_template("home.html")


# -----------------------
# REGISTER
# -----------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":

        existing_user = User.query.filter_by(
            username=request.form["username"]
        ).first()

        if existing_user:
            return "Username already exists. Try another."

        user = User(
            username=request.form["username"],
            password=request.form["password"],
            height=float(request.form["height"]),
            weight=float(request.form["weight"]),
            age=int(request.form["age"]),
            goal=request.form["goal"],
            activity_level=request.form["activity_level"]
        )

        db.session.add(user)
        db.session.commit()
        return redirect("/login")

    return render_template("register.html")


# -----------------------
# LOGIN
# -----------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(
            username=request.form["username"],
            password=request.form["password"]
        ).first()

        if user:
            login_user(user)
            return redirect("/dashboard")

        return "Invalid credentials"

    return render_template("login.html")


# -----------------------
# DASHBOARD
# -----------------------
@app.route("/dashboard")
@login_required
def dashboard():

    sessions = WorkoutSession.query.filter_by(
        user_id=current_user.id
    ).all()

    total_reps = sum(s.reps for s in sessions)
    avg_score = (
        sum(s.avg_score for s in sessions) / len(sessions)
        if sessions else 0
    )

    # Weekly Improvement %
    improvement = 0
    if len(sessions) >= 2:
        first_score = sessions[0].avg_score
        last_score = sessions[-1].avg_score
        if first_score != 0:
            improvement = round(((last_score - first_score) / first_score) * 100, 2)

    latest_risk = HabitRisk.query.filter_by(
        user_id=current_user.id
    ).order_by(HabitRisk.date.desc()).first()

    latest_diet = DietPlan.query.filter_by(
        user_id=current_user.id
    ).order_by(DietPlan.date_updated.desc()).first()

    bmi = round(current_user.weight / ((current_user.height / 100) ** 2), 2)

    diet_info = {
        "bmi": bmi,
        "calories": latest_diet.calories if latest_diet else "N/A",
        "protein": latest_diet.protein if latest_diet else "N/A",
        "carbs": latest_diet.carbs if latest_diet else "N/A",
        "fat": latest_diet.fat if latest_diet else "N/A"
    }

    labels = [s.date.strftime("%d-%m") for s in sessions]
    scores = [s.avg_score for s in sessions]

    return render_template(
        "dashboard.html",
        total_reps=total_reps,
        avg_score=round(avg_score, 2),
        risk=latest_risk.risk_score if latest_risk else "N/A",
        diet=diet_info,
        labels=labels,
        scores=scores,
        improvement=improvement
    )


@app.route("/chat", methods=["GET","POST"])
@login_required
def chat():

    sessions = WorkoutSession.query.filter_by(
        user_id=current_user.id
    ).all()

    latest_risk = HabitRisk.query.filter_by(
        user_id=current_user.id
    ).order_by(HabitRisk.date.desc()).first()

    latest_diet = DietPlan.query.filter_by(
        user_id=current_user.id
    ).order_by(DietPlan.date_updated.desc()).first()

    risk_score = latest_risk.risk_score if latest_risk else 0

    response = None

    if request.method == "POST":
        response = generate_response(
            current_user,
            sessions,
            risk_score,
            latest_diet,
            request.form["message"]
        )

    return render_template("chat.html", response=response)


# -----------------------
# WORKOUT PAGE
# -----------------------
@app.route("/workout")
@login_required
def workout():
    return render_template("workout.html")


@app.route("/start-workout", methods=["POST"])
@login_required
def start_workout():

    exercise = request.form["exercise"]

    if analyze_workout:
        result = analyze_workout(exercise)
    else:
        result = {
            "reps": 10,
            "avg_score": 80,
            "calories": 50,
            "feedback": ["Cloud demo mode – pose detection disabled."]
        }

    session = WorkoutSession(
        user_id=current_user.id,
        exercise=exercise,
        reps=result["reps"],
        avg_score=result["avg_score"],
        calories=result["calories"]
    )
    db.session.add(session)

    workouts_count = WorkoutSession.query.filter_by(
        user_id=current_user.id
    ).count()

    risk = predict_risk(workouts_count, 1, 3, result["avg_score"])

    habit = HabitRisk(
        user_id=current_user.id,
        risk_score=risk
    )
    db.session.add(habit)

    diet_data = calculate_diet(
        current_user.height,
        current_user.weight,
        current_user.age,
        current_user.goal,
        current_user.activity_level
    )

    diet = DietPlan(
        user_id=current_user.id,
        calories=diet_data["calories"],
        protein=diet_data["protein"],
        carbs=diet_data["carbs"],
        fat=diet_data["fats"]
    )

    db.session.add(diet)
    db.session.commit()

    return render_template(
        "workout_result.html",
        reps=result["reps"],
        avg_score=result["avg_score"],
        calories=result["calories"],
        feedback=result["feedback"],
        risk=risk,
        grocery_list=diet_data["grocery_list"]
    )


# -----------------------
# DOWNLOAD REPORT
# -----------------------
@app.route("/download-report")
@login_required
def download_report():

    sessions = WorkoutSession.query.filter_by(
        user_id=current_user.id
    ).all()

    if not sessions:
        return "No workout data available."

    dates = [s.date.strftime("%d-%m") for s in sessions]
    scores = [s.avg_score for s in sessions]
    reps = [s.reps for s in sessions]

    plt.figure()
    plt.plot(dates, scores, marker='o')
    plt.tight_layout()
    plt.savefig("score_graph.png")
    plt.close()

    plt.figure()
    plt.bar(dates, reps)
    plt.tight_layout()
    plt.savefig("reps_graph.png")
    plt.close()

    pdf_path = "fitness_report.pdf"
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph(f"AI Fitness Report - {current_user.username}", styles['Title']))
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(f"Total Reps: {sum(reps)}", styles['Normal']))
    elements.append(Paragraph(f"Average Score: {round(sum(scores)/len(scores),2)}", styles['Normal']))
    elements.append(Spacer(1, 20))
    elements.append(Image("score_graph.png", width=400, height=250))
    elements.append(Spacer(1, 20))
    elements.append(Image("reps_graph.png", width=400, height=250))

    doc.build(elements)

    return send_file(pdf_path, as_attachment=True)


# -----------------------
# LOGOUT
# -----------------------
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")


if __name__ == "__main__":
    app.run()


