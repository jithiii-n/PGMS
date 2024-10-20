import os
import io
import base64
from datetime import datetime, date
from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from werkzeug.security import check_password_hash, generate_password_hash
import matplotlib.pyplot as plt
from utils.db import selectone, iud, select_all
from utils.decorators import admin_required

# Initialize the admin blueprint
admin_bp = Blueprint('admin', __name__)


# Route to display the make announcement page
@admin_bp.route('/makeannouncement', methods=['GET'])
@admin_required
def make_announcement():
    return render_template('makeannouncement.html')


# Route to handle the announcement submission
@admin_bp.route('/submit_announcement', methods=['POST'])
@admin_required
def submit_announcement():
    announcement_text = request.form['announcement']
    ndate = date.today()  # Use today's date as the announcement date

    # SQL query to insert the announcement into the database
    qry = '''
        INSERT INTO announcements (ndate, announcement) VALUES (%s, %s)
    '''

    try:
        iud(qry, (ndate, announcement_text))  # Call your iud function to execute the query
        flash('Announcement submitted successfully.')
    except Exception as e:
        flash(f"An error occurred: {e}")

    # Redirect back to the admin dashboard or an announcements page
    return redirect(url_for('admin.admin_dashboard'))  # Adjust the route as necessary


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
            # Update last_login timestamp
            update_login_time = '''
                UPDATE login
                SET last_login = %s
                WHERE id = %s
            '''
            iud(update_login_time, (datetime.now(), login_user['id']))
            return redirect(url_for('admin.admin_dashboard'))
        else:
            flash('Invalid admin credentials.')

    return render_template('login.html')


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
        officer_name = request.form.get('officer_name')  # New field
        position = request.form.get('position')  # New field

        if not all([id, name, district, email, password]):
            flash("Please fill in all required fields.")
            return redirect(url_for('admin.add_department'))

        # Insert into departments table
        dept_query = '''
            INSERT INTO departments (id, name, district, officer_name, position)
            VALUES (%s, %s, %s, %s, %s)
        '''
        iud(dept_query, (id, name, district, officer_name, position))
        flash('Department added successfully.')

        # Hash the password before storing it
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)

        # Insert into login table with role as NULL for departments
        login_query = '''
            INSERT INTO login (username, password, role)
            VALUES (%s, %s, %s)
        '''
        login_result = iud(login_query, (email, hashed_password, None))  # Role is NULL for departments
        print(f"Login insertion result: {login_result}")

        flash('Department and login details added successfully.')

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


@admin_bp.route('/go_to_add_department', methods=['POST'])
@admin_required
def go_to_add_department():
    return render_template('adddep.html')


@admin_bp.route('/recent_user_activities')
@admin_required
def recent_user_activities():
    # Query to fetch user details and complaint statistics
    qry_users = '''
        SELECT 
            u.lid AS user_id,
            CONCAT(u.fname, ' ', u.lname) AS full_name,
            u.email,
            u.phone,
            u.state,
            COALESCE(COUNT(c.id), 0) AS complaints_filed,
            COALESCE(SUM(CASE WHEN c.status = 'Resolved' THEN 1 ELSE 0 END), 0) AS complaints_resolved
        FROM user u
        LEFT JOIN complaint c ON u.lid = c.lid
        GROUP BY u.lid
        ORDER BY u.lname, u.fname
    '''
    users = select_all(qry_users, ())

    return render_template('recent_user_activities.html', users=users)


@admin_bp.route('/remove_user/<int:user_id>', methods=['POST'])
@admin_required
def remove_user(user_id):
    try:
        # Query to delete the user based on user_id
        delete_user_query = '''
            DELETE FROM user WHERE lid = %s
        '''
        delete_result = iud(delete_user_query, (user_id,))
        if delete_result is not None:
            flash('User removed successfully.')
        else:
            flash('Failed to remove user.')

    except Exception as e:
        flash(f"An error occurred: {e}")
        print(f"An error occurred: {e}")

    return redirect(url_for('admin.recent_user_activities'))


@admin_bp.route('/generated_reports')
@admin_required
def generated_reports():
    # Path to the directory containing the generated reports
    from flask import current_app

    reports_dir = os.path.join(current_app.root_path, 'static/reports')
    reports = os.listdir(reports_dir)

    return render_template('generated_reports.html', reports=reports)
@admin_bp.route('/department_details/<int:dept_id>')
@admin_required
def department_details(dept_id):
    # Query to fetch department details based on dept_id
    qry = '''
        SELECT * FROM departments WHERE id = %s
    '''
    department = selectone(qry, (dept_id,))

    if department:
        return render_template('department_details.html', department=department)
    else:
        flash('Department not found.')
        return redirect(url_for('admin.admin_dashboard'))

