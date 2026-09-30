# app.py
from flask import Flask, render_template, request, redirect, url_for, session
from models import db, PatientLead, InstagramReel, Admin
import os

app = Flask(__name__)
app.secret_key = "vighnaharta_secure_key_2026"

# PythonAnywhere requires an absolute path for SQLite
# Replace 'prathuuu294' with your actual PythonAnywhere username if different
SQLALCHEMY_DATABASE_URI = 'sqlite:////home/vighnahartadentalcare/mysite/clinic.db'
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Create the database tables before the first request
with app.app_context():
    db.create_all()

@app.route('/')
def home():
    # We will fetch active reels here later. For now, just render the page.
    return render_template('index.html')

# (Leave this here, though PythonAnywhere uses the WSGI file to run)
if __name__ == '__main__':
    app.run()
