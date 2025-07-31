import matplotlib
matplotlib.use('Agg') # Use 'Agg' backend for non-interactive plotting (important for server environments)
from flask import Flask, render_template, request, jsonify
import math
import matplotlib.pyplot as plt
import os
import uuid
# from flask import send_from_directory # Not directly used in the API response, but was in original code
# import tempfile # Not directly used in the API response, but was in original code

# Firebase Image URLs (as provided in your original code)
FIREBASE_BMI_IMAGES = {
            1: "https://firebasestorage.googleapis.com/v0/b/muscel-box-09.firebasestorage.app/o/images%2FBMI%2F1.png?alt=media&token=c6278855-60f8-4f7c-9bba-8fa888b2217f",
            2: "https://firebasestorage.googleapis.com/v0/b/muscel-box-09.firebasestorage.app/o/images%2FBMI%2F2.png?alt=media&token=efb71f2f-4663-41ad-8855-95998c01906a",
            3: "https://firebasestorage.googleapis.com/v0/b/muscel-box-09.firebasestorage.app/o/images%2FBMI%2F3.png?alt=media&token=4f3c228b-4660-488c-9788-5120a0141d73",
            4: "https://firebasestorage.googleapis.com/v0/b/muscel-box-09.firebasestorage.app/o/images%2FBMI%2F4.png?alt=media&token=bbea707a-3db1-440c-949a-82f3706aae59",
            5: "https://firebasestorage.googleapis.com/v0/b/muscel-box-09.firebasestorage.app/o/images%2FBMI%2F5.png?alt=media&token=dc5e8c9d-1896-4963-b040-65775a1bb424"
        }
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

# --- Matplotlib Chart Functions (Included for completeness, but not directly used by the API response) ---
def generate_speedometer_gauge(percent, save_path):
    fig, ax = plt.subplots(figsize=(4,2.5), subplot_kw={'projection': 'polar'})
    # Speedometer settings
    min_val, max_val = 0, 50  # 0% to 50% body fat
    theta = (1 - (percent-min_val)/(max_val-min_val)) * 180
    theta_rad = (theta/180) * 3.14159
    # Draw colored arcs
    colors = ['#ff4d4d', '#ffd700', '#ffff66', '#90ee90', '#00cc44']
    ranges = [10, 20, 30, 40, 50]
    start = 0
    for i, r in enumerate(ranges):
        end = r
        ax.barh(1, (end-start)*3.14159/50, left=start*3.14159/50, height=0.5, color=colors[i], alpha=0.7)
        start = end
    # Draw needle
    ax.plot([theta_rad, theta_rad], [0, 1], color='black', lw=3)
    # Add text
    ax.text(0, -0.2, f'Body Fat: {percent:.1f}%', ha='center', va='center', fontsize=12, fontweight='bold')
    # Ticks and labels
    for val in range(0, 51, 10):
        angle = (1 - (val-min_val)/(max_val-min_val)) * 180
        angle_rad = (angle/180) * 3.14159
        ax.text(angle_rad, 1.15, f'{val}%', ha='center', va='center', fontsize=10)
    ax.set_yticklabels([])
    ax.set_xticklabels([])
    ax.set_ylim(0, 1.2)
    ax.axis('off')
    plt.tight_layout()
    plt.savefig(save_path, transparent=True)
    plt.close()

def generate_lean_fat_bar(lean_mass, fat_mass, total_weight, save_path):
    fig, ax = plt.subplots(figsize=(5,1.2))
    ax.barh([''], [lean_mass], color='#3498db', left=0, height=0.5, label='Lean Mass')
    ax.barh([''], [fat_mass], color='#FFD700', left=lean_mass, height=0.5, label='Fat Mass')
    ax.set_xlim(0, total_weight)
    ax.set_xlabel('kg')
    ax.set_title(f'Lean vs Fat Mass ({lean_mass}kg lean, {fat_mass}kg fat)')
    ax.legend(loc='center right')
    plt.tight_layout()
    plt.savefig(save_path, transparent=True)
    plt.close()

app = Flask(__name__)

# --- Helper Calculation Functions ---
def calculate_bmi(weight, height_cm):
    """Calculates Body Mass Index."""
    h = height_cm / 100
    return round(weight / (h ** 2), 1)

def get_bmi_category(bmi):
    """Determines BMI category and provides a message."""
    if bmi < 18.5:
        return 1, "You're underweight – let's add healthy mass!"
    elif bmi < 25:
        return 2, "Perfect! Stay in this healthy range."
    elif bmi < 30:
        return 3, "Slightly overweight – small changes go far!"
    elif bmi < 35:
        return 4, "Obese – time to plan consistent workouts!"
    else:
        return 5, "Extremely obese – health first, step by step!"

def calculate_progress(start, current, target):
    """Calculates weight progress percentage and remaining weight."""
    total = abs(target - start)
    done = abs(current - start)

    # Handle cases where start == target to avoid division by zero or incorrect percentages
    if total == 0:
        percent = 100.0 if current == target else 0.0
    else:
        # Check if progress is in the correct direction
        if (target < start and current <= start and current >= target) or \
           (target > start and current >= start and current <= target):
            percent = (done / total) * 100
        else: # If current weight goes past target or in wrong direction
            percent = 0.0
            if (target < start and current > start) or (target > start and current < start):
                 percent = 0.0 # Or you might want to calculate progress towards start in this case
            elif (target < start and current < target) or (target > start and current > target):
                 percent = 100.0 # If user overshot the target

    remaining = max(total - done, 0)
    return round(min(percent, 100.0), 1), round(remaining, 1)

# This function is no longer directly used in the new weight_progress logic, but kept for completeness
def get_weight_milestones(percent):
    milestones = [20,40,60,80,100]
    count = sum(1 for m in milestones if percent >= m)
    return list(range(1, count+1)) or [1]

def calculate_strength(exercise, sets, reps, weight):
    """Calculates strength level based on exercise volume."""
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
    return 1, "Newbie – let's train!" # Default case

# --- Flask Routes ---
@app.route('/', methods=['GET','POST'])
def index():
    if request.method == 'POST':
        try:
            data = request.form
            gender = data.get('gender', '').strip()
            if not gender:
                return jsonify({'error': 'Gender is required'}), 400
                
            # Convert input data to appropriate types
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
            # Hips circumference is conditional on gender
            hips = float(data.get('hips_circumference', 0)) if gender.lower() == 'female' else 0.0

            # Validate required fields (basic check, can be expanded)
            if not all([height, start_weight, target_weight, current_weight, exercise, sets, reps, weight_lifted, waist, neck]):
                return jsonify({'error': 'All fields are required and must be non-zero'}), 400
            
            # Specific validation for hips if female
            if gender.lower() == 'female' and hips == 0.0:
                 return jsonify({'error': 'Hips circumference is required for female gender'}), 400

        except (ValueError, KeyError) as e:
            return jsonify({'error': f'Invalid input data provided. Please check numeric fields and ensure all required fields are present. Detail: {str(e)}'}), 400

        # --- Calculate BMI ---
        bmi_value = calculate_bmi(current_weight, height)
        bmi_img_id, bmi_msg = get_bmi_category(bmi_value)
        bmi = {
            'value': bmi_value,
            'category': ['Underweight', 'Normal Weight', 'Overweight', 'Obese', 'Extremely Obese'][bmi_img_id - 1],
            'message': bmi_msg,
            'image_url': FIREBASE_BMI_IMAGES.get(bmi_img_id, '') # Adding BMI image directly
        }
        
        # --- Calculate Weight Progress (DEFINITIVELY FIXED) ---
        percent, remaining = calculate_progress(start_weight, current_weight, target_weight)
        
        # Determine the single weight progress image based on percentage
        weight_image_index = 0
        if percent <= 20:
            weight_image_index = 1
        elif percent <= 40:
            weight_image_index = 2
        elif percent <= 60:
            weight_image_index = 3
        elif percent <= 80:
            weight_image_index = 4
        else: # percent > 80, including 100% and above
            weight_image_index = 5
        
        # Get the single image URL
        single_weight_image_url = FIREBASE_WEIGHT_IMAGES.get(weight_image_index, '')

        weight_progress = {
            'progress_percentage': percent,
            'remaining_percentage': round(100 - percent, 1),
            'remaining_kg': remaining,
            'image_url': single_weight_image_url, # This is the ONLY image related key
            'message': f'You have achieved {percent}% of your target! Keep pushing for the remaining {round(100 - percent, 1)}% ({remaining} kg).'
        }
        # --- End Weight Progress Calculation ---

        # --- Calculate Strength ---
        strength_img_id, strength_msg = calculate_strength(exercise, sets, reps, weight_lifted)
        total_volume = sets * reps * weight_lifted
        strength = {
            'total_volume': total_volume,
            'category': ['Beginner', 'Normal', 'Intermediate', 'Advanced', 'Expert'][strength_img_id - 1],
            'image_url': FIREBASE_STRENGTH_IMAGES.get(strength_img_id, ''),
            'message': strength_msg
        }

        # --- Calculate Body Fat Percentage (U.S. Navy Formula) ---
        if gender.lower() == 'male':
            bf = 86.010 * math.log10(waist - neck) - 70.041 * math.log10(height * 0.3937) + 36.76
        else: # Female
            bf = 163.205 * math.log10(waist + hips - neck) - 97.684 * math.log10(height * 0.3937) - 78.387
        
        bf = max(0, round(bf, 1)) # Ensure body fat percentage is not negative

        # Convert current_weight to pounds for lean/fat mass calculation as formula is based on pounds
        current_weight_lbs = current_weight * 2.2046 
        fat_mass_lbs = round((bf * current_weight_lbs) / 100, 1)
        lean_mass_lbs = round(current_weight_lbs - fat_mass_lbs, 1)

        body_fat = {
            'percentage': bf,
            'lean_mass_kg': round(lean_mass_lbs * 0.453592, 1), # Convert back to kg
            'fat_mass_kg': round(fat_mass_lbs * 0.453592, 1),   # Convert back to kg
            'message': 'The U.S. Navy Formula used is fairly accurate for general use but not 100% precise.'
        }

        # --- Return JSON Response ---
        return jsonify({
            'bmi': bmi,
            'weight_progress': weight_progress,
            'strength': strength,
            'body_fat': body_fat,
            'exercise_type': exercise # This was in your original return, so keeping it
        })
    
    # On GET request, return a simple JSON message
    return jsonify({'message': 'API is running. Use POST to submit data to this endpoint.'})

@app.route('/api/calculate', methods=['POST'])
def api_calculate():
    """
    This endpoint also handles POST requests, expecting JSON body.
    It performs the same calculations as the root '/' endpoint.
    """
    data = request.get_json(force=True) # force=True allows parsing even without Content-Type header
    try:
        gender = data.get('gender', '').strip()
        if not gender:
            return jsonify({'error': 'Gender is required'}), 400
        
        # Convert input data to appropriate types
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
        # Hips circumference is conditional on gender
        hips = float(data.get('hips_circumference', 0)) if gender.lower() == 'female' else 0.0

        # Validate required fields (basic check, can be expanded)
        if not all([height, start_weight, target_weight, current_weight, exercise, sets, reps, weight_lifted, waist, neck]):
            return jsonify({'error': 'All fields are required and must be non-zero'}), 400
        
        # Specific validation for hips if female
        if gender.lower() == 'female' and hips == 0.0:
            return jsonify({'error': 'Hips circumference is required for female gender'}), 400

    except (ValueError, KeyError) as e:
        return jsonify({'error': f'Invalid input data provided. Please check numeric fields and ensure all required fields are present. Detail: {str(e)}'}), 400

    # --- Calculate BMI ---
    bmi_value = calculate_bmi(current_weight, height)
    bmi_img_id, bmi_msg = get_bmi_category(bmi_value)
    bmi = {
        'value': bmi_value,
        'category': ['Underweight', 'Normal Weight', 'Overweight', 'Obese', 'Extremely Obese'][bmi_img_id - 1],
        'message': bmi_msg,
        'image_url': FIREBASE_BMI_IMAGES.get(bmi_img_id, '')
    }

    # --- Calculate Weight Progress (DEFINITIVELY FIXED) ---
    percent, remaining = calculate_progress(start_weight, current_weight, target_weight)
    
    # Determine the single weight progress image based on percentage
    weight_image_index = 0
    if percent <= 20:
        weight_image_index = 1
    elif percent <= 40:
        weight_image_index = 2
    elif percent <= 60:
        weight_image_index = 3
    elif percent <= 80:
        weight_image_index = 4
    else: # percent > 80, including 100% and above
        weight_image_index = 5
    
    # Get the single image URL
    single_weight_image_url = FIREBASE_WEIGHT_IMAGES.get(weight_image_index, '')

    weight_progress = {
        'progress_percentage': percent,
        'remaining_percentage': round(100 - percent, 1),
        'remaining_kg': remaining,
        'image_url': single_weight_image_url, # This is the ONLY image related key
        'message': f'You have achieved {percent}% of your target! Keep pushing for the remaining {round(100 - percent, 1)}% ({remaining} kg).'
    }
    # --- End Weight Progress Calculation ---

    # --- Calculate Strength ---
    strength_img_id, strength_msg = calculate_strength(exercise, sets, reps, weight_lifted)
    total_volume = sets * reps * weight_lifted
    strength = {
        'total_volume': total_volume,
        'category': ['Beginner', 'Normal', 'Intermediate', 'Advanced', 'Expert'][strength_img_id - 1],
        'image_url': FIREBASE_STRENGTH_IMAGES.get(strength_img_id, ''),
        'message': strength_msg
    }

    # --- Calculate Body Fat Percentage (U.S. Navy Formula) ---
    if gender.lower() == 'male':
        bf = 86.010 * math.log10(waist - neck) - 70.041 * math.log10(height * 0.3937) + 36.76
    else: # Female
        bf = 163.205 * math.log10(waist + hips - neck) - 97.684 * math.log10(height * 0.3937) - 78.387
    
    bf = max(0, round(bf, 1)) # Ensure body fat percentage is not negative
    
    # Convert current_weight to pounds for lean/fat mass calculation as formula is based on pounds
    current_weight_lbs = current_weight * 2.2046 
    fat_mass_lbs = round((bf * current_weight_lbs) / 100, 1)
    lean_mass_lbs = round(current_weight_lbs - fat_mass_lbs, 1)

    body_fat = {
        'percentage': bf,
        'lean_mass_kg': round(lean_mass_lbs * 0.453592, 1),
        'fat_mass_kg': round(fat_mass_lbs * 0.453592, 1),
        'message': 'The U.S. Navy Formula used is fairly accurate for general use but not 100% precise.'
    }

    # --- Return JSON Response ---
    return jsonify({
        'bmi': bmi,
        'weight_progress': weight_progress,
        'strength': strength,
        'body_fat': body_fat
    })

if __name__=="__main__":
    # For development/testing. In production, use a WSGI server like Gunicorn or uWSGI.
    app.run(debug=True, host='0.0.0.0', port=5000) # debug=True provides useful error messages