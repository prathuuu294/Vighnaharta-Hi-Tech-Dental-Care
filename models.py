# models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False) # We will hash this for security

class PatientLead(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    complaint = db.Column(db.Text, nullable=True)
    preferred_date = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(50), default="New") # Can be 'New', 'Contacted', 'Booked'
    date_submitted = db.Column(db.DateTime, default=datetime.utcnow)

class InstagramReel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reel_url = db.Column(db.String(500), nullable=False) # e.g., 'https://www.instagram.com/reel/C-VfP94P9xH/'
    is_active = db.Column(db.Boolean, default=True)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
