from flask import Blueprint, render_template, redirect, url_for, request, flash, session, send_file, current_app
from werkzeug.utils import secure_filename
import os
from io import BytesIO
from weasyprint import HTML
from utils.db import iud, select_all, selectone
from datetime import datetime
from PIL import Image
import numpy as np

user_bp = Blueprint('user', __name__)

@user_bp.route('/view_complaint/<int:complaint_id>')
def view_complaint(complaint_id):
    # Fetch the complaint details based on the complaint_id
    qry = '''
        SELECT * FROM complaint WHERE id = %s
    '''
    complaint = selectone(qry, (complaint_id,))

    if complaint:
        return render_template('view_complaint.html', complaint=complaint)
    else:
        flash('Complaint not found.')
        return redirect(url_for('user.dashboard'))  # Redirect to dashboard if complaint is not found


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
        qry_check_user = 'SELECT * FROM user WHERE lid = %s'
        user_exists = selectone(qry_check_user, (lid,))
        if not user_exists:
            raise ValueError("User ID does not exist in the user table.")

        # Get form data
        location = request.form.get('location')
        description = request.form.get('description')
        image = request.files.get('image')

        if not location or not description:
            raise ValueError("Location and description are required.")

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

            print(f"Image classified as: {classification}")

        # Map classification to deptid
        classification_to_deptid = {
            'normal': 0,  # Ensure this ID exists in your departments table
            'potholes': 1,  # Ensure this ID exists in your departments table
            'waste': 2  # Or 2, depending on your classification needs
        }

        deptid = classification_to_deptid.get(classification, None)
        if deptid is None:
            raise ValueError(f"Classification '{classification}' is not mapped to a valid department.")

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



@user_bp.route('/download_pdf/<int:complaint_id>')
def download_pdf(complaint_id):
    pdf_filename = f'report_{complaint_id}.pdf'
    pdf_path = os.path.join(current_app.root_path, 'static', 'reports', pdf_filename)
    if os.path.exists(pdf_path):
        return send_file(pdf_path, download_name=pdf_filename, as_attachment=True)
    else:
        flash('Report not found.')
        return redirect(url_for('user.dashboard'))