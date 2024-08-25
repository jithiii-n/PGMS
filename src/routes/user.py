# routes/user.py

from flask import Blueprint, render_template, redirect, url_for, request, flash, session, current_app
from utils.db import iud, select_all, selectone
from utils.decorators import admin_required
from models.model_loader import load_classification_model

from werkzeug.utils import secure_filename
from PIL import Image
import os
import numpy as np
from datetime import datetime

user_bp = Blueprint('user', __name__)

@user_bp.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please log in to view your dashboard.')
        return redirect(url_for('auth.login'))

    # Fetch user complaints
    qry = '''
        SELECT * FROM complaint WHERE lid = %s
    '''
    complaints_list = select_all(qry, (session['user_id'],))
    print(f"User complaints: {complaints_list}")

    return render_template('dashboard.html', complaints=complaints_list)

@user_bp.route('/complaints')
def complaints():
    # Ensure user is logged in
    if 'user_id' not in session:
        flash('Please log in to file a complaint.')
        return redirect(url_for('auth.login'))

    return render_template('complaints.html')

@user_bp.route('/submit_complaint', methods=['POST'])
def submit_complaint():
    try:
        # Get user ID from session
        lid = session.get('user_id')
        print(f"User ID (lid) from session: {lid}")

        if not lid:
            raise ValueError("User ID not found in session.")

        # Check if the user ID exists in the user table
        qry_check_user = '''
            SELECT * FROM user WHERE lid = %s
        '''
        user_exists = selectone(qry_check_user, (lid,))
        print(f"User exists in user table: {user_exists}")

        if not user_exists:
            raise ValueError("User ID does not exist in the user table.")

        # Get form data
        location = request.form.get('location')
        description = request.form.get('description')
        image = request.files.get('image')

        # Ensure the uploads directory exists
        uploads_dir = os.path.join(current_app.root_path, 'static', 'uploads')
        if not os.path.exists(uploads_dir):
            os.makedirs(uploads_dir)

        image_filename = None
        classification = None

        if image:
            image_filename = secure_filename(image.filename)
            image_path = os.path.join(uploads_dir, image_filename)
            image.save(image_path)

            # Load the model
            model = current_app.classification_model

            # Image classification
            img = Image.open(image_path)
            img = img.resize((224, 224))
            img_array = np.array(img) / 255.0
            img_array = np.expand_dims(img_array, axis=0)

            predictions = model.predict(img_array)
            class_labels = ['normal', 'potholes', 'waste']
            classification = class_labels[np.argmax(predictions)]

            # Print classification for debugging
            print(f"Image classified as: {classification}")

        # Map classification to deptid
        classification_to_deptid = {
            'normal': 0,
            'potholes': 1,
            'waste': 2
        }
        deptid = classification_to_deptid.get(classification, 0)  # Default to 0 if classification not found

        # Get the current date
        current_date = datetime.now().strftime('%Y-%m-%d')

        # Insert the complaint into the database
        qry = '''
            INSERT INTO complaint (lid, deptid, date, status, classification, location, description, image_filename)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        '''
        iud(qry, (lid, deptid, current_date, 'Pending', classification, location, description, image_filename))

        flash('Complaint submitted successfully.')
    except Exception as e:
        flash(f"An error occurred: {e}")
        print(f"An error occurred: {e}")

    return redirect(url_for('user.dashboard'))
