from flask import Flask, render_template, request, redirect, url_for, session, send_file
from models import db, PatientLead, InstagramReel, Admin, PatientRecord, Appointment
import os
import uuid
import io
from werkzeug.utils import secure_filename
from fpdf import FPDF
from sqlalchemy import text

app = Flask(__name__)
app.secret_key = "vighnaharta_secure_key_2026"

SQLALCHEMY_DATABASE_URI = 'sqlite:////home/vighnahartadentalcare/mysite/clinic.db'
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static/uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- SECURITY: PREVENT BROWSER CACHING ---
@app.after_request
def add_security_headers(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# --- SAFE AUTO-MIGRATION ENGINE ---
with app.app_context():
    db.create_all()
    if not Admin.query.first():
        default_admin = Admin(username="drpranav", password="securepassword123")
        db.session.add(default_admin)
        db.session.commit()

    try:
        db.session.execute(text("ALTER TABLE patient_record ADD COLUMN appointment_label VARCHAR(50) DEFAULT 'General'"))
        db.session.commit()
    except Exception:
        db.session.rollback()

    legacy_leads = PatientLead.query.filter(PatientLead.appointment_date != None).all()
    for lead in legacy_leads:
        if lead.appointment_date and not lead.appointments:
            new_appt = Appointment(lead_id=lead.id, date_str=lead.appointment_date, label="Appointment 1")
            db.session.add(new_appt)
    db.session.commit()

# --- PUBLIC ROUTES ---
@app.route('/')
def home():
    reels = InstagramReel.query.filter_by(is_active=True).all()
    success = request.args.get('success')
    return render_template('index.html', success=success, reels=reels)

@app.route('/book', methods=['POST'])
def book_consultation():
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        complaint = request.form.get('complaint')
        new_lead = PatientLead(name=name, phone=phone, complaint=complaint)
        db.session.add(new_lead)
        db.session.commit()
        return redirect(url_for('home', success='true'))

# --- SECURE ADMIN ROUTES ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('admin_logged_in'):
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        admin = Admin.query.filter_by(username=username, password=password).first()
        if admin:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('login.html', error="Invalid username or password")
    return render_template('login.html')

@app.route('/reset', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        if request.form.get('security_key') == "Vighnaharta2026":
            admin = Admin.query.filter_by(username=request.form.get('username')).first()
            if admin:
                admin.password = request.form.get('new_password')
                db.session.commit()
                return render_template('login.html', success="Password successfully updated! Please log in.")
            return render_template('reset.html', error="Username not found.")
        return render_template('reset.html', error="Invalid Clinic Master Key.")
    return render_template('reset.html')

@app.route('/admin')
def admin_dashboard():
    if not session.get('admin_logged_in'): return redirect(url_for('login'))
    leads = PatientLead.query.order_by(PatientLead.id.desc()).all()
    reels = InstagramReel.query.order_by(InstagramReel.id.desc()).all()
    return render_template('admin.html', leads=leads, reels=reels)

@app.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('home'))

@app.route('/schedule_lead/<int:lead_id>', methods=['POST'])
def schedule_lead(lead_id):
    if not session.get('admin_logged_in'): return redirect(url_for('login'))

    lead = PatientLead.query.get_or_404(lead_id)
    appt_date = request.form.get('appt_date')
    appt_time = request.form.get('appt_time')
    appt_id_to_edit = request.args.get('appt_id')

    if appt_date and appt_time:
        try:
            from datetime import datetime
            dt_str = f"{appt_date}T{appt_time}"
            formatted_date = datetime.strptime(dt_str, '%Y-%m-%dT%H:%M').strftime('%b %d, %Y at %I:%M %p')
        except Exception:
            formatted_date = f"{appt_date} {appt_time}"

        if appt_id_to_edit and appt_id_to_edit != 'null':
            appt = Appointment.query.get(appt_id_to_edit)
            if appt: appt.date_str = formatted_date
        else:
            count = Appointment.query.filter_by(lead_id=lead.id).count()
            label = f"Appointment {count + 1}"
            new_appt = Appointment(lead_id=lead.id, date_str=formatted_date, label=label)
            db.session.add(new_appt)

        db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/delete_lead/<int:lead_id>')
def delete_lead(lead_id):
    if not session.get('admin_logged_in'): return redirect(url_for('login'))
    db.session.delete(PatientLead.query.get_or_404(lead_id))
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/add_reel', methods=['POST'])
def add_reel():
    if not session.get('admin_logged_in'): return redirect(url_for('login'))
    raw_url = request.form.get('reel_url')
    if raw_url:
        clean = raw_url.split('?')[0]
        if not clean.endswith('/'): clean += '/'
        db.session.add(InstagramReel(reel_url=clean + 'embed'))
        db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/delete_reel/<int:reel_id>')
def delete_reel(reel_id):
    if not session.get('admin_logged_in'): return redirect(url_for('login'))
    db.session.delete(InstagramReel.query.get_or_404(reel_id))
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

# --- CLINICAL RECORDS EHR ENGINE ---
@app.route('/records/<int:lead_id>')
def patient_records(lead_id):
    if not session.get('admin_logged_in'): return redirect(url_for('login'))
    lead = PatientLead.query.get_or_404(lead_id)
    records = PatientRecord.query.filter_by(lead_id=lead_id).order_by(PatientRecord.id.desc()).all()

    appt_dates = {appt.label: appt.date_str for appt in lead.appointments}

    return render_template('records.html', lead=lead, records=records, appt_dates=appt_dates)

@app.route('/upload_record/<int:lead_id>', methods=['POST'])
def upload_record(lead_id):
    if not session.get('admin_logged_in'): return redirect(url_for('login'))

    file = request.files.get('file')
    if file and file.filename:
        original_filename = secure_filename(file.filename)
        secure_name = f"{uuid.uuid4().hex}_{original_filename}"
        file.save(os.path.join(UPLOAD_FOLDER, secure_name))

        appt_label = request.form.get('appointment_label', 'General')

        new_record = PatientRecord(
            lead_id=lead_id,
            file_name=original_filename,
            drive_file_id=secure_name,
            view_link=f"/static/uploads/{secure_name}",
            appointment_label=appt_label
        )
        db.session.add(new_record)
        db.session.commit()

    return redirect(url_for('patient_records', lead_id=lead_id))

@app.route('/rename_record/<int:record_id>', methods=['POST'])
def rename_record(record_id):
    if not session.get('admin_logged_in'): return redirect(url_for('login'))
    record = PatientRecord.query.get_or_404(record_id)
    new_name = request.form.get('new_name')
    if new_name:
        record.file_name = new_name
        db.session.commit()
    return redirect(url_for('patient_records', lead_id=record.lead_id))

@app.route('/delete_record/<int:record_id>')
def delete_record(record_id):
    if not session.get('admin_logged_in'): return redirect(url_for('login'))
    record = PatientRecord.query.get_or_404(record_id)
    file_path = os.path.join(UPLOAD_FOLDER, record.drive_file_id)
    if os.path.exists(file_path): os.remove(file_path)
    lead_id = record.lead_id
    db.session.delete(record)
    db.session.commit()
    return redirect(url_for('patient_records', lead_id=lead_id))

# --- DYNAMIC PDF GENERATOR (PUBLIC, SECURED BY UUID) ---
@app.route('/shared_report/<secure_id>')
def shared_report(secure_id):
    record = PatientRecord.query.filter_by(drive_file_id=secure_id).first_or_404()
    lead = PatientLead.query.get(record.lead_id)

    linked_appt = Appointment.query.filter_by(lead_id=lead.id, label=record.appointment_label).first()
    if linked_appt:
        display_date = linked_appt.date_str.split(' at ')[0]
    else:
        display_date = record.upload_date.strftime('%B %d, %Y')

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=False)

    pdf.set_fill_color(2, 6, 23)
    pdf.rect(0, 0, 210, 42, 'F')

    try:
        pdf.image('https://raw.githubusercontent.com/prathuuu294/Vighnaharta-Hi-Tech-Dental-Care/main/1000727443.png', x=10, y=6, w=30)
    except Exception: pass

    pdf.set_text_color(0, 229, 255)
    pdf.set_font('helvetica', 'B', 18)
    pdf.set_xy(45, 8)
    pdf.cell(155, 10, 'VIGHNAHARTA HI-TECH DENTAL CARE', align='L')

    pdf.set_text_color(255, 255, 255)
    pdf.set_font('helvetica', 'B', 10)
    pdf.set_xy(45, 18)
    pdf.cell(155, 6, 'Dr. Pranav Umarane | BDS (Nair Hospital, Mumbai) | Reg No. : A-58682', align='L')

    pdf.set_font('helvetica', 'I', 9)
    pdf.set_xy(45, 26)
    pdf.cell(155, 6, 'Contact: +91 7666312701 | Annabhau Sathe Chauk, Ambajogai, Maharashtra', align='L')

    pdf.set_y(50)
    pdf.set_fill_color(245, 247, 250)
    pdf.rect(15, 50, 180, 25, 'F')

    pdf.set_text_color(20, 20, 20)
    pdf.set_font('helvetica', 'B', 12)
    pdf.set_xy(20, 53)
    pdf.cell(90, 8, f"Patient: {lead.name}")
    pdf.set_xy(120, 53)

    pdf.cell(70, 8, f"Appt Date: {display_date}", align='R')

    pdf.set_font('helvetica', '', 11)
    pdf.set_xy(20, 61)
    pdf.cell(90, 8, f"Contact: {lead.phone}")
    pdf.set_xy(120, 61)
    pdf.cell(70, 8, f"Visit: {record.appointment_label}", align='R')

    try:
        pdf.set_alpha(0.06)
        pdf.image('https://raw.githubusercontent.com/prathuuu294/Vighnaharta-Hi-Tech-Dental-Care/main/1000727443.png', x=55, y=105, w=100)
        pdf.set_alpha(1.0)
    except Exception: pass

    file_path = os.path.join(UPLOAD_FOLDER, record.drive_file_id)
    if os.path.exists(file_path) and file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
        from PIL import Image
        with Image.open(file_path) as img:
            aspect = img.size[1] / img.size[0]
        img_w = 170
        img_h = img_w * aspect
        if img_h > 145:
            img_h = 145
            img_w = img_h / aspect
        pdf.image(file_path, x=(210 - img_w) / 2, y=85, w=img_w, h=img_h)
    else:
        pdf.set_y(120)
        pdf.set_font('helvetica', 'I', 12)
        pdf.cell(210, 10, '(Clinical Document is in non-image format. View original file.)', align='C')

    pdf.set_y(270)
    pdf.set_font('helvetica', 'I', 9)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(210, 5, 'This is a digitally generated clinical diagnostic report.', align='C')
    pdf.set_y(275)
    pdf.cell(210, 5, 'Vighnaharta Hi-Tech Dental Care, Maharashtra, India', align='C')

    return send_file(io.BytesIO(pdf.output()), mimetype='application/pdf', as_attachment=(True if request.args.get('download') else False), download_name=f"{lead.name.replace(' ', '_')}_{record.file_name}.pdf")

if __name__ == '__main__':
    app.run()
