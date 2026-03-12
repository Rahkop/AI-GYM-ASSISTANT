def estimate_calories_burned(weight, exercise, reps, load=0):
    """
    Estimate calories burned using MET formula.
    MET values:
    - Curl: 6
    - Squat: 8
    - Pushup: 8
    """

    met_values = {
        "curl": 6,
        "squat": 8,
        "pushup": 8
    }

    met = met_values.get(exercise, 6)

    # Estimate duration (seconds per rep ≈ 4)
    duration_minutes = (reps * 4) / 60

    calories = (met * weight * 3.5 / 200) * duration_minutes

    # Add additional energy for weight lifted
    if load > 0:
        calories += load * 0.05

    return round(calories, 2)


def generate_dynamic_instructions(exercise, goal):

    base_instructions = {
        "curl": [
            "Stand upright with dumbbells.",
            "Keep elbows fixed near torso.",
            "Lift weight slowly in 2 seconds.",
            "Lower weight under control."
        ],
        "squat": [
            "Stand shoulder-width apart.",
            "Push hips back and bend knees.",
            "Keep chest upright.",
            "Lower until thighs are parallel."
        ],
        "pushup": [
            "Keep body straight.",
            "Lower chest to floor level.",
            "Engage core muscles.",
            "Push up explosively."
        ]
    }

    goal_modifier = ""
    if goal == "fat_loss":
        goal_modifier = "Use moderate weight with higher repetitions."
    elif goal == "muscle_gain":
        goal_modifier = "Increase resistance progressively."
    else:
        goal_modifier = "Focus on controlled movement and posture."

    return base_instructions.get(exercise, []) + [goal_modifier]


def generate_response(user, sessions, risk, diet, message):

    message = message.lower()

    if not sessions:
        return "Start your first workout to get personalized insights."

    latest_session = sessions[-1]
    exercise = latest_session.exercise
    reps = latest_session.reps

    instructions = generate_dynamic_instructions(exercise, user.goal)

    # Detect calorie question
    if "calorie" in message or "burn" in message:
        estimated_cal = estimate_calories_burned(
            user.weight,
            exercise,
            reps
        )
        return f"You burned approximately {estimated_cal} kcal in your last {exercise} session."

    # Emotional detection
    if "tired" in message or "sad" in message:
        emotion = "I sense fatigue. Reduce intensity but maintain consistency."
    elif "great" in message or "strong" in message:
        emotion = "Fantastic energy! Increase resistance slightly."
    else:
        emotion = "Stay consistent and track weekly progress."

    response = f"""
Last Exercise: {exercise}
Reps: {reps}

Suggested Instructions:
{chr(10).join(["- " + step for step in instructions])}

Habit Risk Score: {risk}

Daily Calories Target: {diet.calories if diet else 'N/A'}

Motivation:
{emotion}
"""

    return response.strip()