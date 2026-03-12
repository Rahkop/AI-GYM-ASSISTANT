def calculate_diet(height, weight, age, goal, activity_level):

    # BMI
    bmi = weight / ((height / 100) ** 2)

    # BMR (Mifflin-St Jeor)
    bmr = 10 * weight + 6.25 * height - 5 * age + 5

    activity_multiplier = {
        "low": 1.2,
        "moderate": 1.55,
        "high": 1.75
    }

    tdee = bmr * activity_multiplier.get(activity_level, 1.2)

    if goal == "fat_loss":
        calories = tdee - 400
        grocery_list = ["Oats", "Eggs", "Chicken Breast", "Spinach", "Almonds"]
    elif goal == "muscle_gain":
        calories = tdee + 400
        grocery_list = ["Rice", "Chicken", "Peanut Butter", "Milk", "Bananas"]
    else:
        calories = tdee
        grocery_list = ["Brown Rice", "Vegetables", "Fruits", "Paneer", "Nuts"]

    protein = weight * 2
    fats = calories * 0.25 / 9
    carbs = (calories - (protein * 4 + fats * 9)) / 4

    return {
        "bmi": round(bmi, 2),
        "calories": round(calories),
        "protein": round(protein),
        "carbs": round(carbs),
        "fats": round(fats),
        "grocery_list": grocery_list
    }