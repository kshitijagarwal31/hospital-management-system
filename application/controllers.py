from flask import Flask, render_template, redirect, request, flash, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date, time, timedelta
from app import app
from .models import *


@app.route("/")
def home():                                                 
    return render_template("home.html")


@app.route("/login", methods = ["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        admin = Admin.query.filter_by(username=username).first()
        if admin and check_password_hash(admin.password, password):
            session["user_id"] = admin.id
            session["role"] = "admin"
            return redirect(url_for("admin_dashboard"))
        
        doctor = Doctor.query.filter_by(username=username).first()
        if doctor and check_password_hash(doctor.password, password):
            if not doctor.is_active:
                flash("Your account has been blacklisted. Contact admin.", "danger")
                return redirect(url_for("login"))
            session["user_id"] = doctor.id
            session["role"] = "doctor"
            return redirect(url_for("doctor_dashboard"))

        patient = Patient.query.filter_by(username=username).first()
        if patient and check_password_hash(patient.password, password):
            if not patient.is_active:
                flash("Your account has been blacklisted. Contact admin.", "danger")
                return redirect(url_for("login"))
            session["user_id"] = patient.id
            session["role"] = "patient"
            return redirect(url_for("patient_dashboard"))

        flash("Invalid username or password", "danger")
        return redirect("/login")
    return render_template("login.html")


@app.route("/register", methods = ["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        name = request.form["name"]
        password = request.form["password"]
        email = request.form["email"]
        phonenumber = request.form["phonenumber"]
        patient_name = Patient.query.filter_by(username=username).first()
        patient_email = Patient.query.filter_by(email=email).first()
        if patient_name and patient_email:
            flash("Patient already exists. Please login.", "warning")
            return redirect("/login")
        else:
            hashed_password = generate_password_hash(password)
            patient = Patient(username=username, name=name, password=hashed_password, email=email, phonenumber=phonenumber)
            db.session.add(patient)
            db.session.commit()
            flash("Registration successful! You can now login.", "success")
            return redirect("/login")   
    return render_template("register.html")


@app.route("/admin_dashboard")
def admin_dashboard():
    admin_id = session.get("user_id")
    if not admin_id:
        return redirect("/login")
    
    admin = Admin.query.get(admin_id)
    doctors = Doctor.query.all()
    patients = Patient.query.all()
    
    today = datetime.today().date()
    
    upcoming = Appointment.query.filter(
        Appointment.status != "Completed"
    ).order_by(Appointment.date.asc(), Appointment.time.asc()).all()

    past = Appointment.query.filter(
        Appointment.status == "Completed"
    ).order_by(Appointment.date.desc(), Appointment.time.desc()).all()

    return render_template("admin_dashboard.html", 
                         admin=admin, 
                         doctors=doctors, 
                         patients=patients,
                         upcoming=upcoming, 
                         past=past)
    

@app.route("/search_doctor_patient")
def search_doctor_patient():
    query = request.args.get("query").strip()
    if query:
        doctors = Doctor.query.filter(
            (Doctor.fullname.ilike(f"%{query}%")) |
            (Doctor.department.ilike(f"%{query}%"))
        ).all()
        patients = Patient.query.filter(
            (Patient.name.ilike(f"%{query}%")) |
            (Patient.phonenumber.ilike(f"%{query}%")) 
        ).all() 
    else:
        doctors = Doctor.query.all()
        patients = Patient.query.all()
    appointments = Appointment.query.all()
    return render_template("admin_dashboard.html", doctors = doctors, patients = patients, appointments = appointments)    

    
@app.route("/add_doctor", methods=["GET", "POST"])
def add_doctor():
    departments = [dept.name for dept in Department.query.all()]

    if request.method == "POST":
        username = request.form["username"]
        fullname = request.form["fullname"]
        password = request.form["password"]
        email = request.form["email"]
        department = request.form["department"].strip()  
        experience = request.form["experience"]

        dept_exists = Department.query.filter_by(name=department).first()

        if not dept_exists:
            flash(f"Department '{department}' does not exist! Please create it first.", "danger")
            return render_template("add_doctor.html", departments=departments)

        if Doctor.query.filter_by(username=username).first():
            flash("Username already taken!", "danger")
        elif Doctor.query.filter_by(email=email).first():
            flash("Email already registered!", "danger")
        else:
            hashed_password = generate_password_hash(password)
            new_doctor = Doctor(
                username=username,
                fullname=fullname,
                password=hashed_password,
                email=email,
                department=department,      
                experience=experience
            )
            db.session.add(new_doctor)
            db.session.commit()
            flash(f"Dr. {fullname} added successfully to {department} department!", "success")
            return redirect(url_for("admin_dashboard"))
    return render_template("add_doctor.html", departments=departments)


@app.route('/add_department', methods=['GET', 'POST'])
def add_department():
    if request.method == 'POST':
        name = request.form['name'].strip()
        overview = request.form.get('overview', '').strip()

        if Department.query.filter_by(name=name).first():
            flash('Department already exists!', 'danger')
        else:
            new_dept = Department(name=name, overview=overview)
            db.session.add(new_dept)
            db.session.commit()
            flash('Department added successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
    return render_template('add_department.html')


@app.route("/edit_doctor/<int:doctor_id>", methods = ["GET", "POST"])
def edit_doctor(doctor_id):
    doctor = Doctor.query.get(doctor_id)
    if request.method == 'POST':
        doctor.username = request.form["username"]
        doctor.fullname = request.form["fullname"]
        doctor.department = request.form["department"]
        doctor.email = request.form["email"] 
        doctor.experience = request.form["experience"]
        if request.form["password"]:
            doctor.password = generate_password_hash(request.form["password"]) 
        db.session.commit()
        flash('Doctor updated successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('edit_doctor.html', doctor=doctor)


@app.route("/delete_doctor/<int:doctor_id>", methods=["POST"])
def delete_doctor(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)
    appointments = Appointment.query.filter_by(doctor_id=doctor_id).all()

    for appt in appointments:
        Treatment.query.filter_by(appointment_id=appt.id).delete()

    Appointment.query.filter_by(doctor_id=doctor_id).delete()
    DoctorAvailability.query.filter_by(doctor_id=doctor_id).delete()
    db.session.delete(doctor)
    db.session.commit()

    flash(f"Dr. {doctor.fullname} deleted successfully!", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/toggle_blacklist_doctor/<int:doctor_id>", methods=["POST"])
def toggle_blacklist_doctor(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)
    doctor.is_active = not doctor.is_active
    db.session.commit()

    status = "Blacklisted" if not doctor.is_active else "Activated (Removed from Blacklist)"
    flash(f"Dr. {doctor.fullname} has been {status}.", "success")
    return redirect(url_for("admin_dashboard"))
    

@app.route("/edit_patient/<int:patient_id>", methods = ["GET", "POST"])
def edit_patient(patient_id):
    patient = Patient.query.get(patient_id)
    if request.method == "POST":
        patient.username = request.form["username"]
        patient.name = request.form["name"]
        patient.email = request.form["email"]
        patient.phonenumber = request.form["phonenumber"]
        if request.form["password"]:
            patient.password = generate_password_hash(request.form["password"])
        db.session.commit()
        flash("Patient profile updated successfully!", "success")
        return redirect(url_for("admin_dashboard"))
    return render_template("edit_patient.html", patient=patient, patient_id = patient.id)


@app.route("/delete_patient/<int:patient_id>", methods=["POST"])
def delete_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    Appointment.query.filter_by(patient_id=patient_id).delete()
    db.session.delete(patient)
    db.session.commit()
    flash(f"Patient {patient.name} deleted successfully!", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/toggle_blacklist_patient/<int:patient_id>", methods = ["POST"])
def toggle_blacklist_patient(patient_id):
    patient = Patient.query.get(patient_id)
    patient.is_active = not patient.is_active
    db.session.commit()
    
    action = "Blacklisted" if not patient.is_active else "Remove form Blacklisted"
    flash(f"{patient.name} has been {action}", "success")
    return redirect(url_for("admin_dashboard")) 
    
    
@app.route("/admin/view_history/<int:patient_id>")
def admin_view_history(patient_id):
    patient = Patient.query.get(patient_id)

    treatments = (
        Treatment.query
        .join(Appointment)
        .join(Doctor)
        .filter(Appointment.patient_id == patient_id)
        .order_by(Appointment.date.desc(), Appointment.time.desc())
        .all()
    )
    return render_template(
        "admin_view_history.html",
        patient=patient,
        treatments=treatments
    )    