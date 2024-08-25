# utils/decorators.py

from functools import wraps
from flask import session, flash, redirect, url_for

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            flash('You need to log in as an admin to access this page.')
            return redirect(url_for('routes.admin.admin_login'))
        return f(*args, **kwargs)
    return decorated_function
