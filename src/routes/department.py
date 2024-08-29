from flask import Blueprint, render_template, redirect, url_for, request, flash, session, send_file, current_app
from werkzeug.utils import secure_filename
import matplotlib.pyplot as plt
import os
from io import BytesIO
from weasyprint import HTML
from utils.db import select_all, selectone, iud
from utils.decorators import department_required

department_bp = Blueprint('department', __name__)


@department_bp.route('/department_dashboard')
@department_required
def department_dashboard():
    dept_id = session.get('department_id')
    if not dept_id:
        flash('Department not logged in.')
        return redirect(url_for('auth.login'))

    qry_complaints = '''
        SELECT * FROM complaint WHERE deptid = %s
    '''
    complaints_list = select_all(qry_complaints, (dept_id,))
    return render_template('dep_dashboard.html', complaints=complaints_list)


@department_bp.route('/view_complaint/<int:complaint_id>')
@department_required
def view_complaint(complaint_id):
    qry = '''
        SELECT * FROM complaint WHERE id = %s
    '''
    complaint = selectone(qry, (complaint_id,))

    if complaint:
        return render_template('view_complaint.html', complaint=complaint)
    else:
        flash('Complaint not found.')
        return redirect(url_for('department.department_dashboard'))



@department_bp.route('/recheck_complaint/<int:complaint_id>', methods=['POST'])
@department_required
def recheck_complaint(complaint_id):
    try:
        qry = '''
            UPDATE complaint SET status = %s WHERE id = %s
        '''
        iud(qry, ('Recheck Image', complaint_id))
        flash('Complaint status updated to "Recheck Image".')
    except Exception as e:
        flash(f"An error occurred: {e}")

    return redirect(url_for('department.department_dashboard'))


@department_bp.route('/report_maker/<int:complaint_id>', methods=['GET', 'POST'])
@department_required
def report_maker(complaint_id):
    if request.method == 'POST':
        # Extract form data
        date = request.form.get('date')
        department = request.form.get('department')
        report_details = request.form.get('report_details')
        additional_info = request.form.get('additional_info')
        officer_name = request.form.get('officer_name')
        reference_no = request.form.get('reference_no')

        # Generate PDF
        pdf_html = render_template('pdf_template.html',
                                   date=date,
                                   department=department,
                                   report_details=report_details,
                                   additional_info=additional_info,
                                   officer_name=officer_name,
                                   reference_no=reference_no)

        pdf = HTML(string=pdf_html).write_pdf()

        # Save PDF to a file
        pdf_filename = f'report_{complaint_id}.pdf'
        pdf_path = os.path.join(current_app.root_path, 'static', 'reports', pdf_filename)
        with open(pdf_path, 'wb') as f:
            f.write(pdf)

        flash('Report generated and saved successfully.')
        return redirect(url_for('department.department_dashboard'))

    # For GET requests, fetch complaint details
    qry = '''
        SELECT * FROM complaint WHERE id = %s
    '''
    complaint = selectone(qry, (complaint_id,))

    if complaint:
        return render_template('reportmaker.html', complaint=complaint)
    else:
        flash('Complaint not found.')
        return redirect(url_for('department.department_dashboard'))


@department_bp.route('/mark_resolved/<int:complaint_id>', methods=['POST'])
@department_required
def mark_resolved(complaint_id):
    try:
        # Update the complaint status to "Resolved"
        qry = '''
            UPDATE complaint SET status = %s WHERE id = %s
        '''
        iud(qry, ('Resolved', complaint_id))
        flash('Complaint marked as resolved.')

        # Redirect to the reportmaker.html page
        return redirect(url_for('department.report_maker', complaint_id=complaint_id))
    except Exception as e:
        flash(f"An error occurred: {e}")
        return redirect(url_for('department.department_dashboard'))

@department_bp.route('/department_logout', methods=['POST'])
def department_logout():
    session.pop('department_id', None)
    flash('Department has been logged out.')
    return redirect(url_for('auth.login'))
