# routes/admin.py
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from flask import Blueprint, render_template, redirect, url_for, request, flash
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash
import io
import base64
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
    # Query to fetch the 3 latest complaints with department names
    qry_complaints = '''
        SELECT c.*, d.name AS department_name
        FROM complaint c
        JOIN departments d ON c.deptid = d.id
        ORDER BY c.date DESC
        LIMIT 3
    '''
    latest_complaints = select_all(qry_complaints, ())

    # Query to fetch total count of complaints for pagination
    qry_total_complaints = '''
        SELECT COUNT(*) AS total_count
        FROM complaint
    '''
    total_count_result = selectone(qry_total_complaints, ())
    total_count = total_count_result['total_count']

    return render_template('admin_dashboard.html', complaints=latest_complaints, total_count=total_count)






@admin_bp.route('/add_department', methods=['POST'])
@admin_required
def add_department():
    try:
        id = request.form.get('id')  # Fetch the Department ID
        name = request.form.get('name')
        district = request.form.get('district')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        if not all([id, name, district, email, password]):
            flash("Please fill in all required fields.")
            return redirect(url_for('admin.add_department'))

        # Insert into departments table
        dept_query = '''
            INSERT INTO departments (id, name, district)
            VALUES (%s, %s, %s)
        '''
        iud(dept_query, (id, name, district))
        flash('Department added successfully.')

        # Hash the password before storing it
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)

        # Insert into login table
        login_query = '''
            INSERT INTO login (username, password, role)
            VALUES (%s, %s, %s)
        '''
        login_result = iud(login_query, (email, hashed_password, role))
        print(f"Login insertion result: {login_result}")

        flash('Department and login details added successfully.')

    except Exception as e:
        flash(f"An error occurred: {e}")
        print(f"An error occurred: {e}")

    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/add_department_page')
@admin_required
def add_department_page():
    return render_template('adddep.html')


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
    return redirect(url_for('auth.login'))


@admin_bp.route('/analysis/<int:dept_id>')
@admin_required
def analysis(dept_id):
    # Query to fetch the number of resolved complaints and total number of complaints
    qry = '''
        SELECT 
            SUM(CASE WHEN status = 'Resolved' THEN 1 ELSE 0 END) AS resolved_count,
            COUNT(*) AS total_count
        FROM complaint
        WHERE deptid = %s
    '''
    performance_data = selectone(qry, (dept_id,))

    if not performance_data:
        flash("No performance data available for the selected department.")
        return redirect(url_for('admin.admin_dashboard'))

    # Extract counts
    resolved_count = performance_data['resolved_count']
    total_count = performance_data['total_count']

    # Plotting the bar chart
    plt.figure(figsize=(8, 6))
    categories = ['Resolved Complaints', 'Total Complaints']
    counts = [resolved_count, total_count]

    plt.bar(categories, counts, color=['green', 'blue'])
    plt.xlabel('Complaint Status')
    plt.ylabel('Number of Complaints')
    plt.title('Comparison of Resolved Complaints to Total Complaints')

    # Save the plot to a string buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()

    # Convert the plot to a base64 string for embedding in HTML
    chart_data = base64.b64encode(buf.getvalue()).decode('utf8')
    buf.close()

    return render_template('analysis.html', chart_data=chart_data)


@admin_bp.route('/show_more_complaints')
@admin_required
def show_more_complaints():
    # Query to fetch all complaints with department names, excluding the latest 3
    qry_complaints = '''
        SELECT c.*, d.name AS department_name
        FROM complaint c
        JOIN departments d ON c.deptid = d.id
        ORDER BY c.date DESC
    '''
    all_complaints = select_all(qry_complaints, ())
    return render_template('show_more_complaints.html', complaints=all_complaints)
