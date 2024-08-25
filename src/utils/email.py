# utils/email.py

import requests
from flask import current_app

def send_email(to_email, subject, html_content):
    response = requests.post(
        'https://api.brevo.com/v3/smtp/email',
        headers={
            'Content-Type': 'application/json',
            'api-key': current_app.config['BREVO_API_KEY']
        },
        json={
            'sender': {'email': '23mp2138@rit.ac.in'},  # Replace with your sender email
            'to': [{'email': to_email}],
            'subject': subject,
            'htmlContent': html_content
        }
    )
    return response.status_code == 201
