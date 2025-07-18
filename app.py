import matplotlib
matplotlib.use('Agg')
from flask import Flask, render_template, request, jsonify
import math
import matplotlib.pyplot as plt
import os
import uuid
from flask import send_from_directory
import tempfile

# --- NEW: Speedometer and Bar Chart Functions ---
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
app.config['SECRET_KEY'] = 'MnvXDQaVtWXtjBp2y0PwWEr_6IVoLpUZUGEBtZ3MiMM'

def calculate_bmi(weight, height_cm):
    h = height_cm / 100
    return round(weight / (h ** 2), 1)

def get_bmi_category(bmi):
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
    total = abs(target - start)
    done = current - start
    percent = min((done/total)*100 if total else 0, 100)
    if done < 0:
        return round(0,1), round(0,1)
    else :
        return round(percent,1), round(total - done,1)

def get_weight_milestones(percent):
    milestones = [20,40,60,80,100]
    count = sum(1 for m in milestones if percent >= m)
    return list(range(1, count+1)) or [1]

def calculate_strength(exercise, sets, reps, weight):
    volume = sets*reps*weight
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

@app.route('/', methods=['GET','POST'])
def index():
    if request.method == 'POST':
        try:
            data = request.form
            gender = data.get('gender', '').strip()
            if not gender:
                return render_template('index.html', error='Gender is required')
                
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
            hips = float(data.get('hips_circumference', 0)) if gender=='female' else 0
            # Validate required fields
            if not all([height, start_weight, target_weight, current_weight, exercise, sets, reps, weight_lifted, waist, neck]):
                return render_template('index.html', error='All fields are required')
        except (ValueError, KeyError) as e:
            return render_template('index.html', error=f'Invalid input data - {str(e)}')

        # Calculate BMI
        bmi_value = calculate_bmi(current_weight, height)
        bmi_img, bmi_msg = get_bmi_category(bmi_value)
        bmi = {
            'value': bmi_value,
            'category': ['Underweight', 'Normal Weight', 'Overweight', 'Obese', 'Extremely Obese'][bmi_img - 1],
            'image': f'images/BMI/{bmi_img}.png',
            'message': bmi_msg
        }
        # Calculate weight progress
        percent, remaining = calculate_progress(start_weight, current_weight, target_weight)
        # Weight gain images and fixed percents logic
        if percent <= 20:
            weight_images = ['1.png']
            weight_percents = [percent]
        elif 20 < percent <= 40:
            weight_images = ['1.png', '2.png']
            weight_percents = [20, percent]
        elif 40 < percent <= 60:
            weight_images = ['1.png', '2.png', '3.png']
            weight_percents = [20, 40, percent]
        elif 60 < percent <= 80:
            weight_images = ['1.png', '2.png', '3.png', '4.png']
            weight_percents = [20, 40, 60, percent]
        elif 80 < percent < 100:
            weight_images = ['1.png', '2.png', '3.png', '4.png', '5.png']
            weight_percents = [20, 40, 60, 80, percent]
        else:  # percent >= 100
            weight_images = ['1.png', '2.png', '3.png', '4.png', '5.png']
            weight_percents = [20, 40, 60, 80, 100]
        milestone_images = [f'images/weights/{img}' for img in weight_images]
        milestone_percents = weight_percents
        milestones = list(zip(milestone_images, milestone_percents))
        weight_progress = {
            'progress_percentage': percent,
            'remaining_percentage': round(100 - percent, 1),
            'remaining_kg': remaining,
            'milestones': milestones,
            'message': f'You have achieved {percent}% of your target! Keep pushing for the remaining {round(100 - percent, 1)}% ({remaining} kg).'
        }
        strength_img, strength_msg = calculate_strength(exercise, sets, reps, weight_lifted)
        total_volume = sets * reps * weight_lifted
        strength = {
            'total_volume': total_volume,
            'category': ['Beginner', 'Normal', 'Intermediate', 'Advanced', 'Expert'][strength_img - 1],
            'image': f'images/strength/{strength_img}.png',
            'message': strength_msg
        }
        # Calculate body fat percentage using new formulas
        if gender == 'male':
            # U.S. Navy formula for men
            bf = 86.010 * math.log10(waist - neck) - 70.041 * math.log10(height * 0.3937) + 36.76
        else:
            # U.S. Navy formula for women
            bf = 163.205 * math.log10(waist + hips - neck) - 97.684 * math.log10(height * 0.3937) - 78.387
        bf = max(0, round(bf, 1))
        fat_mass = round((bf * current_weight * 2.2046) / 100, 1)
        lean_mass = round((current_weight * 2.2046) - fat_mass, 1)

        body_fat = {
            'percentage': bf,
            'lean_mass_kg': lean_mass * 0.45359,
            'fat_mass_kg': fat_mass * 0.45359,
            'message': 'The  Formula used is fairly accurate for general use but not 100% precise.'
        }
        # Only show results, not the form, after POST
        return render_template('index.html', bmi=bmi, weight_progress=weight_progress, strength=strength, body_fat=body_fat, show_form=False, exercise_type=exercise)
    # On GET, show the form
    return render_template('index.html', show_form=True)

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
        hips = float(data.get('hips_circumference', 0)) if gender=='female' else 0
        if not all([height, start_weight, target_weight, current_weight, exercise, sets, reps, weight_lifted, waist, neck]):
            return jsonify({'error': 'All fields are required'}), 400
    except (ValueError, KeyError) as e:
        return jsonify({'error': f'Invalid input data - {str(e)}'}), 400

    # BMI
    bmi_value = calculate_bmi(current_weight, height)
    bmi_img, bmi_msg = get_bmi_category(bmi_value)
    bmi = {
        'value': bmi_value,
        'category': ['Underweight', 'Normal Weight', 'Overweight', 'Obese', 'Extremely Obese'][bmi_img - 1],
        'image': f'images/BMI/{bmi_img}.png',
        'message': bmi_msg
    }
    # Weight progress
    percent, remaining = calculate_progress(start_weight, current_weight, target_weight)
    if percent <= 20:
        weight_images = ['1.png']
        weight_percents = [percent]
    elif 20 < percent <= 40:
        weight_images = ['1.png', '2.png']
        weight_percents = [20, percent]
    elif 40 < percent <= 60:
        weight_images = ['1.png', '2.png', '3.png']
        weight_percents = [20, 40, percent]
    elif 60 < percent <= 80:
        weight_images = ['1.png', '2.png', '3.png', '4.png']
        weight_percents = [20, 40, 60, percent]
    elif 80 < percent < 100:
        weight_images = ['1.png', '2.png', '3.png', '4.png', '5.png']
        weight_percents = [20, 40, 60, 80, percent]
    else:
        weight_images = ['1.png', '2.png', '3.png', '4.png', '5.png']
        weight_percents = [20, 40, 60, 80, 100]
    milestone_images = [f'images/weights/{img}' for img in weight_images]
    milestone_percents = weight_percents
    milestones = list(zip(milestone_images, milestone_percents))
    weight_progress = {
        'progress_percentage': percent,
        'remaining_percentage': round(100 - percent, 1),
        'remaining_kg': remaining,
        'milestones': milestones,
        'message': f'You have achieved {percent}% of your target! Keep pushing for the remaining {round(100 - percent, 1)}% ({remaining} kg).'
    }
    # Strength
    strength_img, strength_msg = calculate_strength(exercise, sets, reps, weight_lifted)
    total_volume = sets * reps * weight_lifted
    strength = {
        'total_volume': total_volume,
        'category': ['Beginner', 'Normal', 'Intermediate', 'Advanced', 'Expert'][strength_img - 1],
        'image': f'images/strength/{strength_img}.png',
        'message': strength_msg
    }
    # Body fat
    if gender == 'male':
        bf = 86.010 * math.log10(waist - neck) - 70.041 * math.log10(height * 0.3937) + 36.76
    else:
        bf = 163.205 * math.log10(waist + hips - neck) - 97.684 * math.log10(height * 0.3937) - 78.387
    bf = max(0, round(bf, 1))
    fat_mass = round((bf * current_weight * 2.2046) / 100, 1)
    lean_mass = round((current_weight * 2.2046) - fat_mass, 1)
    body_fat = {
        'percentage': bf,
        'lean_mass_kg': lean_mass * 0.45359,
        'fat_mass_kg': fat_mass * 0.45359,
        'message': 'The  Formula used is fairly accurate for general use but not 100% precise.'
    }
    return jsonify({
        'bmi': bmi,
        'weight_progress': weight_progress,
        'strength': strength,
        'body_fat': body_fat
    })

if __name__=="__main__":
    # Only for development/testing! Use a WSGI server for production.
    app.run(debug=False)
