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