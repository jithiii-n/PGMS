from flask import Blueprint, render_template, redirect, url_for, request, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from utils.db import iud, selectone
from utils.email import send_email
import secrets
from flask import current_app
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def index():
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            # Retrieve form data
            fname = request.form.get('fname')
            lname = request.form.get('lname')
            email = request.form.get('email')
            password = request.form.get('password')
            phone = request.form.get('phone')
            state = request.form.get('state')

            if not all([fname, lname, email, password]):
                flash("Please fill in all required fields.")
                return redirect(url_for('auth.register'))

            hashed_password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)

            # Insert into the user table
            qry_user = '''
                INSERT INTO user (fname, lname, email, phone, state)
                VALUES (%s, %s, %s, %s, %s)
            '''
            user_id = iud(qry_user, (fname, lname, email, phone, state))
            print(f"User ID after inserting into user table: {user_id}")

            if user_id:
                # Insert into the login table
                qry_login = '''
                    INSERT INTO login (username, password)
                    VALUES (%s, %s)
                '''
                login_id = iud(qry_login, (email, hashed_password))
                print(f"Login ID after inserting into login table: {login_id}")

                if login_id:
                    flash("Registration successful. Please log in.")
                    return redirect(url_for('auth.login'))
                else:
                    flash("Error inserting into login table. Please try again.")
            else:
                flash("Error during registration. Please try again.")

        except Exception as e:
            flash(f"An error occurred: {e}")
            print(f"An error occurred: {e}")

    return render_template('registration.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email').strip()
        password = request.form.get('password').strip()

        if not email or not password:
            flash('Email and password are required.')
            return redirect(url_for('auth.login'))

        try:
            qry_login = '''
                SELECT * FROM login WHERE username = %s
            '''
            login_user = selectone(qry_login, (email,))
            print(f"Login user: {login_user}")  # Debugging statement

            if login_user and check_password_hash(login_user['password'], password):
                print(f"User role: {login_user.get('role')}")  # Debugging statement
                if login_user.get('role') == 'admin':
                    session['admin_id'] = login_user['id']  # Set session for admin
                    print(f"Session admin_id set to: {session.get('admin_id')}")  # Debugging statement
                    return redirect(url_for('admin.admin_dashboard'))
                elif login_user.get('role') == 'department':
                    session['department_id'] = login_user.get('department_id')  # Set session for department
                    print(f"Session department_id set to: {session.get('department_id')}")  # Debugging statement
                    return redirect(url_for('department.department_dashboard'))
                else:
                    # Regular user login
                    qry_user = '''
                        SELECT lid FROM user WHERE email = %s
                    '''
                    user = selectone(qry_user, (email,))
                    if user:
                        session['user_id'] = user['lid']  # Set session for regular user
                        print(f"Session user_id set to: {session.get('user_id')}")  # Debugging statement
                        return redirect(url_for('user.dashboard'))
                    else:
                        flash('User not found in user table.')
            else:
                flash('Invalid login credentials.')

        except Exception as e:
            flash(f"An error occurred: {e}")
            print(f"An error occurred: {e}")

    return render_template('login.html')

@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    session.pop('admin_id', None)
    session.pop('department_id', None)
    flash('You have been logged out.')
    return redirect(url_for('auth.login'))

@auth_bp.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')

        # Check if the email exists in the database
        qry = '''
            SELECT * FROM login WHERE username = %s
        '''
        user = selectone(qry, (email,))

        if user:
            # Generate a reset token and link
            token = secrets.token_urlsafe()
            reset_link = url_for('auth.reset_password', token=token, _external=True)

            # Store the token in the database
            qry_token = '''
                INSERT INTO password_reset_tokens (email, token, created_at)
                VALUES (%s, %s, %s)
            '''
            iud(qry_token, (email, token, datetime.now()))

            # Send email via Brevo
            email_sent = send_email(
                to_email=email,
                subject='Password Reset Request',
                html_content=f'<p>Click the following link to reset your password: <a href="{reset_link}">{reset_link}</a></p>'
            )

            if email_sent:
                flash('Password reset link has been sent to your email.')
            else:
                flash('Failed to send password reset email.')

        else:
            flash('Email not found.')

        return redirect(url_for('auth.login'))

    return render_template('forgot_password.html')

@auth_bp.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    token = request.args.get('token')
    if request.method == 'POST':
        new_password = request.form.get('password')

        # Hash the new password
        hashed_password = generate_password_hash(new_password, method='pbkdf2:sha256', salt_length=16)

        # Verify token and get email
        qry_token = '''
            SELECT * FROM password_reset_tokens WHERE token = %s
        '''
        token_data = selectone(qry_token, (token,))

        if token_data:
            email = token_data['email']

            # Update the password in the database
            qry_update = '''
                UPDATE login SET password = %s WHERE username = %s
            '''
            update_status = iud(qry_update, (hashed_password, email))

            # Remove the used token
            qry_remove_token = '''
                DELETE FROM password_reset_tokens WHERE token = %s
            '''
            iud(qry_remove_token, (token,))

            # Send confirmation email via Brevo
            email_sent = send_email(
                to_email=email,
                subject='Password Reset Successful',
                html_content='<p>Your password has been successfully reset.</p>'
            )

            if email_sent:
                flash('Your password has been reset successfully.')
            else:
                flash('Failed to send confirmation email.')

            return redirect(url_for('auth.login'))
        else:
            flash('Invalid or expired token.')

    return render_template('reset_password.html', token=token)
