from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

class PatientLead(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    complaint = db.Column(db.Text, nullable=True)
    preferred_date = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(50), default="New")
    date_submitted = db.Column(db.DateTime, default=datetime.utcnow)
    appointment_date = db.Column(db.String(100), nullable=True) # Legacy keeping for safety

    # Links a single patient to infinite appointments
    appointments = db.relationship('Appointment', backref='patient', lazy=True, cascade="all, delete-orphan")

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lead_id = db.Column(db.Integer, db.ForeignKey('patient_lead.id'), nullable=False)
    date_str = db.Column(db.String(100), nullable=False)
    label = db.Column(db.String(50), nullable=False) # e.g., "Appointment 1"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class InstagramReel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reel_url = db.Column(db.String(500), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)

class PatientRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lead_id = db.Column(db.Integer, nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    drive_file_id = db.Column(db.String(255), nullable=False)
    view_link = db.Column(db.String(500), nullable=False)
    appointment_label = db.Column(db.String(50), default="General") # Links record to specific visit
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)