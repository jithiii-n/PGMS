# routes/admin.py

from flask import Blueprint, render_template, redirect, url_for, request, flash
from werkzeug.security import check_password_hash
from utils.db import selectone, iud, select_all
from utils.decorators import admin_required
from flask import session

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        qry_login = '''
            SELECT * FROM login WHERE username = %s
        '''
        login_user = selectone(qry_login, (username,))

        if login_user and check_password_hash(login_user['password'], password) and login_user.get('role') == 'admin':
            session['admin_id'] = login_user['id']
            return redirect(url_for('admin.admin_dashboard'))
        else:
            flash('Invalid admin credentials.')

    return render_template('admin_login.html')

@admin_bp.route('/admin_dashboard')
@admin_required
def admin_dashboard():
    qry_complaints = '''
        SELECT * FROM complaint
    '''
    complaints_list = select_all(qry_complaints, ())
    return render_template('admin_dashboard.html', complaints=complaints_list)

@admin_bp.route('/add_department', methods=['POST'])
@admin_required
def add_department():
    try:
        lid = request.form.get('lid')
        name = request.form.get('name')
        district = request.form.get('district')

        qry = '''
            INSERT INTO departments (lid, name, district)
            VALUES (%s, %s, %s)
        '''
        iud(qry, (lid, name, district))

        flash('Department added successfully.')
    except Exception as e:
        flash(f"An error occurred: {e}")
        print(f"An error occurred: {e}")

    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/view_complaint/<int:complaint_id>')
@admin_required
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
        return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/admin_logout', methods=['POST'])
def admin_logout():
    session.pop('admin_id', None)
    flash('Admin has been logged out.')
    return redirect(url_for('auth.admin_login'))
