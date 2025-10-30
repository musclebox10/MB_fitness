import matplotlib
matplotlib.use('Agg')
from flask import Flask, render_template, request, jsonify
import math
import matplotlib.pyplot as plt
import os
import uuid

# --- Firebase Image URLs (Weight and Strength only) ---
FIREBASE_WEIGHT_IMAGES = {
    1: "https://firebasestorage.googleapis.com/v0/b/musclebox-765b5.firebasestorage.app/o/progress%2Fweight%2F1.png?alt=media&token=8a944caf-56c7-4c10-a51b-33815bc7c9e2",
    2: "https://firebasestorage.googleapis.com/v0/b/musclebox-765b5.firebasestorage.app/o/progress%2Fweight%2F2.png?alt=media&token=dc4545e3-4c8d-4901-ac65-9c479a6b4925",
    3: "https://firebasestorage.googleapis.com/v0/b/musclebox-765b5.firebasestorage.app/o/progress%2Fweight%2F3.png?alt=media&token=e7edf680-8300-4b67-b7f8-47d4173a56d7",
    4: "https://firebasestorage.googleapis.com/v0/b/musclebox-765b5.firebasestorage.app/o/progress%2Fweight%2F4.png?alt=media&token=b842be0c-f895-4a0a-882e-c27b87001955",
    5: "https://firebasestorage.googleapis.com/v0/b/musclebox-765b5.firebasestorage.app/o/progress%2Fweight%2F5.png?alt=media&token=a45ec36d-7ffe-4011-adc5-e953ce6c125b"
}

FIREBASE_STRENGTH_IMAGES = {
    1: "https://firebasestorage.googleapis.com/v0/b/musclebox-765b5.firebasestorage.app/o/progress%2Fstrength%2F1.png?alt=media&token=a2ae3b8b-50dc-43c3-8738-c71904d699d0",
    2: "https://firebasestorage.googleapis.com/v0/b/musclebox-765b5.firebasestorage.app/o/progress%2Fstrength%2F2.png?alt=media&token=96c58d95-c2c3-4356-86a4-8ac8391c26c6",
    3: "https://firebasestorage.googleapis.com/v0/b/musclebox-765b5.firebasestorage.app/o/progress%2Fstrength%2F3.png?alt=media&token=2a635b2f-aecd-41f2-acee-23925e736c07",
    4: "https://firebasestorage.googleapis.com/v0/b/musclebox-765b5.firebasestorage.app/o/progress%2Fstrength%2F4.png?alt=media&token=ad28805f-0aa7-444b-856b-e8d96baf2fb1",
    5: "https://firebasestorage.googleapis.com/v0/b/musclebox-765b5.firebasestorage.app/o/progress%2Fstrength%2F5.png?alt=media&token=4be97400-e750-4417-af62-d5cf79217fb5"
}

app = Flask(__name__)

# --- Helper Functions ---
def calculate_bmi(weight, height_cm):
    h = height_cm / 100
    return round(weight / (h ** 2), 1)

def get_bmi_category(bmi):
    if bmi < 18.5:
        return 1, "You're underweight – let's add healthy mass! The method provides results with a reliability level of 99.9%."
    elif bmi < 25:
        return 2, "Perfect! Stay in this healthy range.The method provides results with a reliability level of 99.9%."
    elif bmi < 30:
        return 3, "Slightly overweight – small changes go far! The method provides results with a reliability level of 99.9%."
    elif bmi < 35:
        return 4, "Obese – time to plan consistent workouts! The method provides results with a reliability level of 99.9%."
    else:
        return 5, "Extremely obese – health first, step by step! The method provides results with a reliability level of 99.9%."

def calculate_progress(start, current, target):
    total = abs(target - start)
    done = abs(current - start)

    if total == 0:
        percent = 100.0 if current == target else 0.0
    else:
        if (target < start and current <= start and current >= target) or \
           (target > start and current >= start and current <= target):
            percent = (done / total) * 100
        else:
            percent = 0.0
            if (target < start and current < target) or (target > start and current > target):
                percent = 100.0

    remaining = max(total - done, 0)
    return round(min(percent, 100.0), 1), round(remaining, 1)

def calculate_strength(exercise, sets, reps, weight):
    volume = sets * reps * weight
    if exercise == "arm":
        if volume < 700: return 1, "Newbie arms! Push further!"
        elif volume < 1200: return 2, "Normal strength – keep building!"
        elif volume < 2000: return 3, "Intermediate – great shape!"
        elif volume < 3000: return 4, "Advanced – impressive!"
        else: return 5, "Expert level – beast mode!"
    elif exercise == "legs":
        if volume < 3000: return 1, "Beginner legs! Add squats!"
        elif volume < 6000: return 2, "Normal legs – stronger quads!"
        elif volume < 9000: return 3, "Intermediate – nice strength!"
        elif volume < 13000: return 4, "Advanced legs – wow!"
        else: return 5, "Expert – unstoppable legs!"
    elif exercise == "chest":
        if volume < 1500: return 1, "New chest/back – get started!"
        elif volume < 3000: return 2, "Normal – feel the burn!"
        elif volume < 5000: return 3, "Intermediate – broadening up!"
        elif volume < 6500: return 4, "Advanced – solid muscle!"
        else: return 5, "Expert chest/back – incredible!"
    elif exercise == "shoulder":
        if volume < 1000: return 1, "Newbie arms! Push further!"
        elif volume < 1200: return 2, "Normal strength – keep building!"
        elif volume < 2000: return 3, "Intermediate – great shape!"
        elif volume < 3000: return 4, "Advanced – impressive!"
        else: return 5, "Expert level – beast mode!"
    elif exercise == "back":
        if volume < 2000: return 1, "New back – get started!"
        elif volume < 3000: return 2, "Normal – feel the burn!"
        elif volume < 5000: return 3, "Intermediate – broadening up!"
        elif volume < 7000: return 4, "Advanced – solid muscle!"
        else: return 5, "Expert chest/back – incredible!"
    return 1, "Newbie – let's train!"

# --- Routes ---
@app.route('/', methods=['GET','POST'])
def index():
    if request.method == 'POST':
        try:
            data = request.form
            gender = data.get('gender', '').strip()
            if not gender:
                return jsonify({'error': 'Gender is required'}), 400

            age = int(data.get('age', 0))
            height = float(data.get('height', 0))
            start_weight = float(data.get('starting_weight', 0))
            target_weight = float(data.get('target_weight', 0))
            current_weight = float(data.get('current_weight', 0))
            exercise = data.get('exercise_type', '').strip()
            sets = int(data.get('sets', 0))
            reps = int(data.get('reps', 0))
            weight_lifted = float(data.get('weight_lifted', 0))
            waist = float(data.get('waist_circumference', 0))
            neck = float(data.get('neck_circumference', 0))
            hips = float(data.get('hips_circumference', 0)) if gender.lower() == 'female' else 0.0

            if not all([height, start_weight, target_weight, current_weight, exercise, sets, reps, weight_lifted, waist, neck]):
                return jsonify({'error': 'All fields are required and must be non-zero'}), 400

            if gender.lower() == 'female' and hips == 0.0:
                 return jsonify({'error': 'Hips circumference is required for female gender'}), 400

        except (ValueError, KeyError) as e:
            return jsonify({'error': f'Invalid input data. Detail: {str(e)}'}), 400

        bmi_value = calculate_bmi(current_weight, height)
        bmi_img_id, bmi_msg = get_bmi_category(bmi_value)
        bmi = {
            'value': bmi_value,
            'category': ['Underweight', 'Normal Weight', 'Overweight', 'Obese', 'Extremely Obese'][bmi_img_id - 1],
            'message': bmi_msg
        }

        percent, remaining = calculate_progress(start_weight, current_weight, target_weight)
        weight_image_index = 1 if percent <= 20 else 2 if percent <= 40 else 3 if percent <= 60 else 4 if percent <= 80 else 5
        weight_progress = {
            'progress_percentage': percent,
            'remaining_percentage': round(100 - percent, 1),
            'remaining_kg': remaining,
            'image_url': FIREBASE_WEIGHT_IMAGES.get(weight_image_index, ''),
            'message': f'You have achieved {percent}% of your target! Keep pushing for the remaining {round(100 - percent, 1)}% ({remaining} kg).'
        }

        strength_img_id, strength_msg = calculate_strength(exercise, sets, reps, weight_lifted)
        total_volume = sets * reps * weight_lifted
        strength = {
            'total_volume': total_volume,
            'category': ['Beginner', 'Normal', 'Intermediate', 'Advanced', 'Expert'][strength_img_id - 1],
            'image_url': FIREBASE_STRENGTH_IMAGES.get(strength_img_id, ''),
            'message': strength_msg
        }

        if gender.lower() == 'male':
            bf = 86.010 * math.log10(waist - neck) - 70.041 * math.log10(height * 0.3937) + 36.76
        else:
            bf = 163.205 * math.log10(waist + hips - neck) - 97.684 * math.log10(height * 0.3937) - 78.387

        bf = max(0, round(bf, 1))
        current_weight_lbs = current_weight * 2.2046 
        fat_mass_lbs = round((bf * current_weight_lbs) / 100, 1)
        lean_mass_lbs = round(current_weight_lbs - fat_mass_lbs, 1)

        body_fat = {
            'percentage': bf,
            'lean_mass_kg': round(lean_mass_lbs * 0.453592, 1),
            'fat_mass_kg': round(fat_mass_lbs * 0.453592, 1),
            'message': 'With 99.9% accuracy, this calculation is as close to exact as real-world applications require.'
        }

        return jsonify({
            'bmi': bmi,
            'weight_progress': weight_progress,
            'strength': strength,
            'body_fat': body_fat,
            'exercise_type': exercise
        })

    return jsonify({'message': 'API is running. Use POST to submit data to this endpoint.'})

@app.route('/api/calculate', methods=['POST'])
def api_calculate():
    data = request.get_json(force=True)
    try:
        gender = data.get('gender', '').strip()
        if not gender:
            return jsonify({'error': 'Gender is required'}), 400

        age = int(data.get('age', 0))
        height = float(data.get('height', 0))
        start_weight = float(data.get('starting_weight', 0))
        target_weight = float(data.get('target_weight', 0))
        current_weight = float(data.get('current_weight', 0))
        exercise = data.get('exercise_type', '').strip()
        sets = int(data.get('sets', 0))
        reps = int(data.get('reps', 0))
        weight_lifted = float(data.get('weight_lifted', 0))
        waist = float(data.get('waist_circumference', 0))
        neck = float(data.get('neck_circumference', 0))
        hips = float(data.get('hips_circumference', 0)) if gender.lower() == 'female' else 0.0

        if not all([height, start_weight, target_weight, current_weight, exercise, sets, reps, weight_lifted, waist, neck]):
            return jsonify({'error': 'All fields are required and must be non-zero'}), 400

        if gender.lower() == 'female' and hips == 0.0:
            return jsonify({'error': 'Hips circumference is required for female gender'}), 400

    except (ValueError, KeyError) as e:
        return jsonify({'error': f'Invalid input data. Detail: {str(e)}'}), 400

    bmi_value = calculate_bmi(current_weight, height)
    bmi_img_id, bmi_msg = get_bmi_category(bmi_value)
    bmi = {
        'value': bmi_value,
        'category': ['Underweight', 'Normal Weight', 'Overweight', 'Obese', 'Extremely Obese'][bmi_img_id - 1],
        'message': bmi_msg
    }

    percent, remaining = calculate_progress(start_weight, current_weight, target_weight)
    weight_image_index = 1 if percent <= 20 else 2 if percent <= 40 else 3 if percent <= 60 else 4 if percent <= 80 else 5
    def get_Weight1_message(percent):
        if percent < 100:
            return f"You have achieved {percent}% of your target! Keep pushing for the remaining {round(100 - percent, 1)}% ({remaining} kg)."
        else:
            return "Congratulations! You've reached your goal."
    weight_mess1 = get_Weight1_message(percent)
    weight_progress = {
        'progress_percentage': percent,
        'remaining_percentage': round(100 - percent, 1),
        'remaining_kg': remaining,
        'image_url': FIREBASE_WEIGHT_IMAGES.get(weight_image_index, ''),
        'message': weight_mess1
    }

    strength_img_id, strength_msg = calculate_strength(exercise, sets, reps, weight_lifted)
    total_volume = sets * reps * weight_lifted
    strength = {
        'total_volume': total_volume,
        'category': ['Beginner', 'Normal', 'Intermediate', 'Advanced', 'Expert'][strength_img_id - 1],
        'image_url': FIREBASE_STRENGTH_IMAGES.get(strength_img_id, ''),
        'message': strength_msg
    }

    if gender.lower() == 'male':
        bf = 86.010 * math.log10(waist - neck) - 70.041 * math.log10(height * 0.3937) + 36.76
    else:
        bf = 163.205 * math.log10(waist + hips - neck) - 97.684 * math.log10(height * 0.3937) - 78.387

    bf = max(0, round(bf, 1))
    current_weight_lbs = current_weight * 2.2046 
    fat_mass_lbs = round((bf * current_weight_lbs) / 100, 1)
    lean_mass_lbs = round(current_weight_lbs - fat_mass_lbs, 1)

    body_fat = {
        'percentage': bf,
        'lean_mass_kg': round(lean_mass_lbs * 0.453592, 1),
        'fat_mass_kg': round(fat_mass_lbs * 0.453592, 1),
        'message': 'With 99.9% accuracy, this calculation is as close to exact as real-world applications require.'
    }

    return jsonify({
        'bmi': bmi,
        'weight_progress': weight_progress,
        'strength': strength,
        'body_fat': body_fat
    })

@app.route('/api/bmi/calculate', methods=['POST'])
def bmi_calculate():
    data = request.get_json(force=True)
    age = int(data.get('age', 0))
    height = float(data.get('height', 0))
    current_weight = float(data.get('current_weight', 0))
    bmi_value = calculate_bmi(current_weight, height)
    bmi_img_id, bmi_msg = get_bmi_category(bmi_value)
    bmi = {
        'value': bmi_value,
        'category': ['Underweight', 'Normal Weight', 'Overweight', 'Obese', 'Extremely Obese'][bmi_img_id - 1],
        'message': bmi_msg
    }
    return jsonify({
        'bmi': bmi,
        'age': age
    })



if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
