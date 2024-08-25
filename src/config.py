# config.py

import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_secret_key'  # Replace with a secure key
    BREVO_API_KEY = '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'
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
