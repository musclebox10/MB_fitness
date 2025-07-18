# Fitness Tracker App

A simple web-based fitness tracker built with Flask. It calculates BMI, weight progress, strength level, and body fat percentage, and provides motivational feedback and visuals.

## Features
- BMI calculation and category
- Weight progress tracking with milestone images
- Strength level calculation based on exercise input
- Body fat percentage, lean mass, and fat mass calculation
- Responsive, modern UI

## Requirements
- Python 3.x
- Flask

## Setup & Run
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the app:
   ```bash
   python app.py
   ```
3. Open your browser and go to [http://127.0.0.1:5000/](http://127.0.0.1:5000/)

## Directory Structure
- `app.py` - Main Flask application
- `templates/index.html` - Main HTML template
- `static/css/style.css` - Stylesheet
- `static/images/` - Images for BMI, strength, and weight progress

## Notes
- For development, you can set `debug=True` in `app.py`.
- All calculations are for educational purposes only. 

## Production Deployment

1. Install dependencies:
   ```sh
   pip install -r requirements.txt
   pip install waitress
   ```
2. Run the app with Waitress (WSGI server):
   ```sh
   waitress-serve --port=5000 internship.fitness_app.app:app
   ```
   (Adjust the import path if needed.)

## Pushing to Git
- Make sure you do not commit sensitive files or test files.
- Recommended: add `.env` for secrets (if needed in future).
- Commit and push your changes:
   ```sh
   git add .
   git commit -m "Production ready setup with WSGI server"
   git push
   ``` 