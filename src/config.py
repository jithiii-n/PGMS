# config.py

import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_secret_key'  # Replace with a secure key
    #BREVO_API_KEY = removed for security
    MAIL_SERVER = 'smtp-relay.brevo.com'
    MAIL_PORT = 587
    MAIL_USERNAME = '7ae371001@smtp-brevo.com'
    MAIL_PASSWORD = 'zvGYTH1Q5KAsfN94'
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    UPLOAD_FOLDER = os.path.join('static', 'uploads')
    DATABASE = {
        'host': 'localhost',
        'port': 3306,
        'user': 'root',
        'password': '',
        'db': 'pgms'
    }
