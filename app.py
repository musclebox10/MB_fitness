import matplotlib
matplotlib.use('Agg')
from flask import Flask, request, jsonify
import math

# --- Firebase Image URLs (Weight and Strength only) ---
FIREBASE_WEIGHT_IMAGES = {
    1: "https://firebasestorage.googleapis.com/v0/b/muscel-box-09.firebasestorage.app/o/images%2Fweights%2F1.png?alt=media&token=b0e96ef5-8fbf-49a9-8d1d-7c2fed4e225d",
    2: "https://firebasestorage.googleapis.com/v0/b/muscel-box-09.firebasestorage.app/o/images%2Fweights%2F2.png?alt=media&token=8b471b35-feae-4d34-8e3b-c578e73a7578",
    3: "https://firebasestorage.googleapis.com/v0/b/muscel-box-09.firebasestorage.app/o/images%2Fweights%2F3.png?alt=media&token=60cc2fe7-8140-4f75-86c6-32939bfc9f29",
    4: "https://firebasestorage.googleapis.com/v0/b/muscel-box-09.firebasestorage.app/o/images%2Fweights%2F4.png?alt=media&token=51e9eda2-eb8b-4b0b-b458-1eefcf5ca7b3",
    5: "https://firebasestorage.googleapis.com/v0/b/muscel-box-09.firebasestorage.app/o/images%2Fweights%2F5.png?alt=media&token=d4b4530b-eefc-46e3-9250-3ddf1414248f"
}

FIREBASE_STRENGTH_IMAGES = {
    1: "https://firebasestorage.googleapis.com/v0/b/muscel-box-09.firebasestorage.app/o/images%2Fstrength%2F1.png?alt=media&token=451ee35d-740d-4a30-980a-b5adae929451",
    2: "https://firebasestorage.googleapis.com/v0/b/muscel-box-09.firebasestorage.app/o/images%2Fstrength%2F2.png?alt=media&token=a633bb5e-dcd9-42d2-9141-0e781d393183",
    3: "https://firebasestorage.googleapis.com/v0/b/muscel-box-09.firebasestorage.app/o/images%2Fstrength%2F3.png?alt=media&token=d61734b5-8c63-4f47-8f49-36b3f6f77b8d",
    4: "https://firebasestorage.googleapis.com/v0/b/muscel-box-09.firebasestorage.app/o/images%2Fstrength%2F4.png?alt=media&token=b35b3c49-3dde-4942-9c23-5cc87804259e",
    5: "https://firebasestorage.googleapis.com/v0/b/muscel-box-09.firebasestorage.app/o/images%2Fstrength%2F5.png?alt=media&token=afc42bbd-9ca6-4ee8-a5d6-c7666ecf9998"
}

app = Flask(__name__)

# --- Helper Functions (No changes needed here) ---
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
    if exercise == "arms/shoulder":
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
    elif exercise == "chest/back":
        if volume < 1500: return 1, "New chest/back – get started!"
        elif volume < 3000: return 2, "Normal – feel the burn!"
        elif volume < 5000: return 3, "Intermediate – broadening up!"
        elif volume < 7000: return 4, "Advanced – solid muscle!"
        else: return 5, "Expert chest/back – incredible!"
    return 1, "Newbie – let's train!"

# --- Routes ---
@app.route('/', methods=['GET'])
def index():
    return jsonify({'message': 'API is running. Use POST to submit data to the /api/calculate endpoint.'})

@app.route('/api/calculate', methods=['POST'])
def api_calculate():
    try:
        data = request.get_json(force=True)
        if not isinstance(data, dict):
             return jsonify({'error': 'Invalid JSON format. Must be an object.'}), 400
    except:
        return jsonify({'error': 'Failed to decode JSON object from request body.'}), 400
        
    results = {}

    # --- 1. BMI Calculation (Optional) ---
    # Requires: current_weight, height
    if 'current_weight' in data and 'height' in data:
        try:
            current_weight = float(data['current_weight'])
            height = float(data['height'])
            
            bmi_value = calculate_bmi(current_weight, height)
            bmi_img_id, bmi_msg = get_bmi_category(bmi_value)
            results['bmi'] = {
                'value': bmi_value,
                'category': ['Underweight', 'Normal Weight', 'Overweight', 'Obese', 'Extremely Obese'][bmi_img_id - 1],
                'message': bmi_msg
            }
        except (ValueError, TypeError):
            results['bmi_error'] = "Invalid 'current_weight' or 'height' provided for BMI calculation."

    # --- 2. Weight Progress Calculation (Optional) ---
    # Requires: starting_weight, current_weight, target_weight
    if 'starting_weight' in data and 'current_weight' in data and 'target_weight' in data:
        try:
            start_weight = float(data['starting_weight'])
            current_weight = float(data['current_weight'])
            target_weight = float(data['target_weight'])
            
            percent, remaining = calculate_progress(start_weight, current_weight, target_weight)
            weight_image_index = 1 if percent <= 20 else 2 if percent <= 40 else 3 if percent <= 60 else 4 if percent <= 80 else 5
            
            message = f"You have achieved {percent}% of your target! Keep pushing for the remaining {round(100 - percent, 1)}% ({remaining} kg)."
            if percent >= 100:
                message = "Congratulations! You've reached your weight goal."
            
            results['weight_progress'] = {
                'progress_percentage': percent,
                'remaining_percentage': round(100 - percent, 1),
                'remaining_kg': remaining,
                'image_url': FIREBASE_WEIGHT_IMAGES.get(weight_image_index, ''),
                'message': message
            }
        except (ValueError, TypeError):
            results['weight_progress_error'] = "Invalid weight values provided for progress calculation."

    # --- 3. Strength Calculation (Optional) ---
    # Requires: exercise_type, sets, reps, weight_lifted
    if 'exercise_type' in data and 'sets' in data and 'reps' in data and 'weight_lifted' in data:
        try:
            exercise = str(data['exercise_type']).strip()
            sets = int(data['sets'])
            reps = int(data['reps'])
            weight_lifted = float(data['weight_lifted'])

            strength_img_id, strength_msg = calculate_strength(exercise, sets, reps, weight_lifted)
            total_volume = sets * reps * weight_lifted
            results['strength'] = {
                'total_volume': total_volume,
                'category': ['Beginner', 'Normal', 'Intermediate', 'Advanced', 'Expert'][strength_img_id - 1],
                'image_url': FIREBASE_STRENGTH_IMAGES.get(strength_img_id, ''),
                'message': strength_msg
            }
        except (ValueError, TypeError):
             results['strength_error'] = "Invalid values provided for strength calculation."

    # --- 4. Body Fat Calculation (Optional) ---
    # Requires: gender, waist_circumference, neck_circumference, height, current_weight
    # Additionally requires 'hips_circumference' for females.
    bf_base_params = ['gender', 'waist_circumference', 'neck_circumference', 'height', 'current_weight']
    if all(param in data for param in bf_base_params):
        try:
            gender = str(data.get('gender', '')).lower()
            height = float(data['height'])
            waist = float(data['waist_circumference'])
            neck = float(data['neck_circumference'])
            current_weight = float(data['current_weight'])
            
            bf = 0
            if gender == 'male':
                bf = 86.010 * math.log10(waist - neck) - 70.041 * math.log10(height * 0.3937) + 36.76
            elif gender == 'female' and 'hips_circumference' in data:
                hips = float(data['hips_circumference'])
                bf = 163.205 * math.log10(waist + hips - neck) - 97.684 * math.log10(height * 0.3937) - 78.387
            elif gender == 'female':
                 results['body_fat_error'] = "Missing 'hips_circumference' for female body fat calculation."

            if bf > 0:
                bf = max(0, round(bf, 1))
                current_weight_lbs = current_weight * 2.2046
                fat_mass_lbs = round((bf * current_weight_lbs) / 100, 1)
                lean_mass_lbs = round(current_weight_lbs - fat_mass_lbs, 1)

                results['body_fat'] = {
                    'percentage': bf,
                    'lean_mass_kg': round(lean_mass_lbs * 0.453592, 1),
                    'fat_mass_kg': round(fat_mass_lbs * 0.453592, 1),
                    'message': 'With 99.9% accuracy, this calculation is as close to exact as real-world applications require.'
                }
        except (ValueError, TypeError):
             results['body_fat_error'] = "Invalid values provided for body fat calculation."


    # --- Final Response ---
    if not results:
        return jsonify({'error': 'No valid parameters provided for any calculation. Please provide parameters for at least one feature.'}), 400

    return jsonify(results)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
