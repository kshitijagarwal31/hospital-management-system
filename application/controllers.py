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
    
    
@app.route("/patient_dashboard")
def patient_dashboard():
    if session.get("role") != "patient":
        flash("Please login as patient", "danger")
        return redirect(url_for("login"))

    patient_id = session["user_id"]
    patient = Patient.query.get_or_404(patient_id)

    appointments = Appointment.query.filter(
        Appointment.patient_id == patient_id,
        Appointment.date >= date.today(),
        Appointment.status.in_(["Booked", "Confirmed"])
    ).order_by(Appointment.date.asc(), Appointment.time.asc()).all()

    departments = Department.query.all()
    active_doctors = Doctor.query.filter_by(is_active=True).all()

    return render_template(
        "patient_dashboard.html",
        patient=patient,
        appointments=appointments,
        departments=departments,
        doctors=active_doctors
    )


@app.route("/patient_history")
def patient_history():
    patient_id = session['user_id']
    patient = Patient.query.get_or_404(patient_id)

    treatments = (Treatment.query
                  .filter_by(patient_id=patient_id)
                  .order_by(Treatment.date.desc(), Treatment.time.desc())
                  .all())
    doctor = None
    if treatments:
        doctor = Doctor.query.get(treatments[0].doctor_id)
    return render_template("patient_history.html",
                           patient=patient,
                           doctor=doctor,        
                           treatments=treatments)


@app.route('/doctors/<dept>')
def doctors_department(dept):
    department_name = dept.replace('_', ' ').title()
    
    department_obj = Department.query.filter(
        Department.name.ilike(department_name)
    ).first_or_404()
    
    doctors = [
        doc for doc in Doctor.query.all() 
        if doc.department and doc.department.strip().lower() == department_name.lower()
    ]
    overview = department_obj.overview or "No description available for this department."
    return render_template('doctors_department.html',
                         doctors=doctors,
                         department_name=department_name,
                         overview=overview)


@app.route("/patient/availability/<int:doctor_id>", methods=["GET", "POST"])
def patient_view_doctor_availability(doctor_id):
    if session.get("role") != "patient":
        flash("Please login as patient", "danger")
        return redirect(url_for("login"))

    doctor = Doctor.query.get_or_404(doctor_id)

    if not doctor.is_active:
        flash("This doctor is currently unavailable for booking.", "warning")
        return redirect(url_for("patient_dashboard"))

    today = date.today()
    seven_days = [today + timedelta(days=i) for i in range(7)]

    if request.method == "POST":
        slot_value = request.form.get("slot")
        if not slot_value:
            flash("Please select a time slot!", "danger")
            return redirect(request.url)

        try:
            date_str, time_str = slot_value.split("|")
            selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            selected_time = time_str.strip()

            slot = DoctorAvailability.query.filter_by(
                doctor_id=doctor_id,
                date=selected_date,
                time=selected_time,
                status="available"
            ).with_for_update().first()

            if not slot:
                flash("Sorry, this slot was just booked by someone else!", "danger")
                return redirect(request.url)

            slot.status = "booked"
            appointment = Appointment(
                patient_id=session["user_id"],
                doctor_id=doctor_id,
                date=selected_date,
                time=selected_time,
                status="Booked",
                department=doctor.department
            )
            db.session.add(appointment)
            db.session.commit()

            flash(f"Appointment booked successfully on {selected_date.strftime('%d %B %Y')} at {format_time(selected_time)}!", "success")
            return redirect(url_for("patient_dashboard"))

        except Exception as e:
            db.session.rollback()
            flash("Booking failed. Please try again.", "danger")
            print("BOOKING ERROR:", e)
            return redirect(request.url)

    all_slots = DoctorAvailability.query.filter(
        DoctorAvailability.doctor_id == doctor_id,
        DoctorAvailability.date.in_(seven_days)
    ).order_by(DoctorAvailability.date, DoctorAvailability.time).all()

    slots_by_date = {}
    for day in seven_days:
        day_str = day.strftime("%Y-%m-%d")
        slots_by_date[day_str] = [s for s in all_slots if s.date.strftime("%Y-%m-%d") == day_str]

    return render_template(
        "patient_view_doctor_availability.html",
        doctor=doctor,
        seven_days=seven_days,
        slots_by_date=slots_by_date,
        format_time=format_time
    )


@app.route('/doctor/<username>')
def doctor_profile(username):
    if session.get("role") != "patient":
        flash("Please login as patient.", "danger")
        return redirect(url_for("login"))

    doctor = Doctor.query.filter_by(username=username).first()

    if not doctor:
        flash("Doctor not found.", "danger")
        return redirect(url_for("patient_dashboard"))
    return render_template('doctor_profile.html', doctor=doctor)


@app.route("/edit_patient_profile/<int:patient_id>", methods = ["GET", "POST"])
def edit_patient_profile(patient_id):
    patient = Patient.query.get(patient_id)
    if request.method == "POST":
        patient.username = request.form["username"]
        patient.name = request.form["name"]
        patient.email = request.form["email"]
        patient.phonenumber = request.form["phonenumber"]
        if request.form["password"]:
            patient.password = generate_password_hash(request.form["password"])
        db.session.commit()
        return redirect(url_for("patient_dashboard"))
    return render_template("edit_patient_profile.html", patient=patient, patient_id = patient_id)
    
    
@app.route("/doctor_dashboard")
def doctor_dashboard():
    if session.get("role") != "doctor" or "user_id" not in session:
        return redirect(url_for("login"))

    doctor = Doctor.query.get(session["user_id"])
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)

    weekly_appointments = Appointment.query.filter(
        Appointment.doctor_id == doctor.id,
        Appointment.date >= start_of_week,
        Appointment.date <= end_of_week,
        Appointment.status.in_(["Booked", "Confirmed"]) 
    ).order_by(Appointment.date, Appointment.time).all()

    for appt in weekly_appointments:
        appt.has_treatment = Treatment.query.filter_by(appointment_id=appt.id).first() is not None

    assigned_patients = Patient.query\
        .join(Treatment, Treatment.patient_id == Patient.id)\
        .join(Appointment, Appointment.id == Treatment.appointment_id)\
        .filter(
            Appointment.doctor_id == doctor.id,
            Appointment.status == "Completed" 
        ).distinct().all()

    return render_template(
        "doctor_dashboard.html",
        doctor=doctor,
        appointments=weekly_appointments,
        patients=assigned_patients
    )


@app.route("/appointment/<int:id>/complete", methods=["POST"])
def mark_completed(id):
    appt = Appointment.query.get_or_404(id)

    if session.get("role") != "doctor" or appt.doctor_id != session["user_id"]:
        flash("Unauthorized action!", "danger")
        return redirect(url_for("doctor_dashboard"))

    if appt.status not in ["Booked", "Confirmed"]:
        flash("This appointment cannot be completed.", "warning")
        return redirect(url_for("doctor_dashboard"))

    slot = DoctorAvailability.query.filter_by(
        doctor_id=appt.doctor_id,
        date=appt.date,
        time=appt.time
    ).first()

    if slot:
        slot.status = "available"
    
    appt.status = "Completed"

    try:
        db.session.commit()
        flash(f"Appointment completed! Slot is now available for new bookings.", "success")
    except Exception as e:
        db.session.rollback()
        flash("Error completing appointment.", "danger")
        print("ERROR:", e)

    return redirect(url_for("doctor_dashboard"))


@app.route("/cancel_appointment/<int:appt_id>", methods=["POST"])
def cancel_appointment(appt_id):
    if 'user_id' not in session:
        flash("Please login first!", "danger")
        return redirect(url_for("login"))

    appt = Appointment.query.get_or_404(appt_id)

    user_role = session.get('role')
    user_id = session['user_id']

    if user_role == 'patient' and appt.patient_id != user_id:
        flash("You can only cancel your own appointments!", "danger")
        return redirect(url_for("patient_dashboard"))

    if user_role == 'doctor' and appt.doctor_id != user_id:
        flash("You can only cancel your own appointments!", "danger")
        return redirect(url_for("doctor_dashboard"))

    if user_role not in ['patient', 'doctor']:
        flash("Unauthorized!", "danger")
        return redirect(url_for("login"))

    slot = DoctorAvailability.query.filter_by(
        doctor_id=appt.doctor_id,
        date=appt.date,
        time=appt.time
    ).first()

    if slot:
        slot.status = "available" 

    db.session.delete(appt)
    db.session.commit()

    flash("Appointment cancelled successfully! Slot is now available for booking.", "success")

    if user_role == 'patient':
        return redirect(url_for("patient_dashboard"))
    else:
        return redirect(url_for("doctor_dashboard"))
    
    
@app.route("/appointment/<int:id>/cancel", methods= ["POST"])
def mark_cancelled(id):
    appt = Appointment.query.get(id)
    if appt.status == "Booked":
        appt.status = "Cancelled"
    db.session.commit()
    return redirect("/doctor_dashboard") 


@app.route("/update_patient_history/<int:appointment_id>", methods=["GET", "POST"])
def update_patient_history(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    patient = Patient.query.get(appointment.patient_id)
    doctor = Doctor.query.get(appointment.doctor_id)

    if request.method == "POST":
        diagnosis = request.form["diagnosis"]
        prescription = request.form["prescription"]
        notes = request.form["notes"]

        existing_treatment = Treatment.query.filter_by(appointment_id=appointment.id).first()
        if not existing_treatment:
            treatment = Treatment(
                date=appointment.date,
                time=appointment.time,
                diagnosis=diagnosis,
                prescription=prescription,
                notes=notes,
                appointment_id=appointment.id,
                patient_id=patient.id,
                doctor_id=appointment.doctor_id
            )
            db.session.add(treatment)
            db.session.commit() 

            flash("Treatment saved successfully! Now mark as complete when done.", "success")
        else:
            flash("Treatment already exists!", "info")

        return redirect(url_for("doctor_dashboard"))
    return render_template("update_patient_history.html", 
                         patient=patient, 
                         appointment=appointment, 
                         doctor=doctor)


@app.route("/update/<int:doctor_id>/doctor/availability", methods=["GET", "POST"])
def update_doctor_availability(doctor_id):

    if request.method == "POST":
        selected_slots = []

        DoctorAvailability.query.filter_by(doctor_id=doctor_id).delete()
        
        for key, value in request.form.items():
          selected_slots.append(value)

        for item in selected_slots:
            date_str, time = item.split("|")  
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()

            new_slot = DoctorAvailability(
                doctor_id=doctor_id,
                date=date_obj,
                time=time,
                status="available"
            )
            db.session.add(new_slot)

        db.session.commit()

        return redirect(url_for("doctor_dashboard", doctor_id=doctor_id))

    today = datetime.today()
    seven_days = [today + timedelta(days=i) for i in range(7)]

    saved = DoctorAvailability.query.filter_by(doctor_id=doctor_id).all()
    saved_set = set([f"{a.date}|{a.time}" for a in saved])

    return render_template(
        "update_doctor_availability.html",
        doctor_id=doctor_id,
        seven_days=seven_days,
        saved_set=saved_set
    )


@app.route("/view_patient_history/<int:patient_id>/<int:doctor_id>")
def view_patient_history(patient_id, doctor_id):
    patient = Patient.query.get(patient_id)
    appointment = Appointment.query.filter_by(patient_id=patient_id).order_by(Appointment.date.desc(), Appointment.time.desc()).first()
    doctor = Doctor.query.get(appointment.doctor_id)
    treatments = Treatment.query.join(Appointment).filter(Appointment.patient_id == patient_id, Appointment.doctor_id == doctor_id).order_by(Appointment.date.desc(), Appointment.time.desc()).all()
    return render_template("view_patient_history.html", patient=patient, treatments=treatments, doctor=doctor)


@app.template_filter('format_time')
def format_time(time_str):
    if not time_str:
        return "N/A"
    try:
        t = datetime.strptime(time_str, "%H:%M")
        return t.strftime("%I:%M %p") 
    except:
        return time_str