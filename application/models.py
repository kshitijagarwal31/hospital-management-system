from .database import db



class Admin(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(100), unique = True, nullable = False)
    password = db.Column(db.String(200), nullable = False)
    email = db.Column(db.String(100), unique = True) 


class Patient(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(100), unique = True, nullable = False)
    name = db.Column(db.String(100), nullable = False)
    password = db.Column(db.String(200), nullable = False)
    email = db.Column(db.String(100), unique = True)
    phonenumber = db.Column(db.String(12), nullable = False)
    appointments = db.relationship('Appointment', backref = "patient", lazy = True)
    is_active = db.Column(db.Boolean, default = True)

    
class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(100), unique = True, nullable = False)
    fullname = db.Column(db.String(100), nullable = False)
    password = db.Column(db.String(200), nullable = False)
    email = db.Column(db.String(100), unique = True)
    experience = db.Column(db.Integer, nullable= False)
    department = db.Column(db.String(100))    
    is_active = db.Column(db.Boolean, default = True)
    department_id = db.Column(db.Integer, db.ForeignKey("department.id"))
    appointments = db.relationship("Appointment", backref = "doctor", lazy = True)


class DoctorAvailability(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.String(50), nullable=False) 
    status = db.Column(db.String(20), default='available') 
    doctor_rel = db.relationship('Doctor', backref='availabilities')
    
class Department(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(100), nullable=False)
    overview = db.Column(db.Text)
    doctors = db.relationship("Doctor", backref="dept", lazy=True)

    
class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    date = db.Column(db.Date, nullable = False)
    time = db.Column(db.String(50), nullable = False)
    status = db.Column(db.String(20), default = "Booked")
    department = db.Column(db.String(50), nullable = False)
    patient_id = db.Column(db.Integer, db.ForeignKey("patient.id"), nullable = False)
    doctor_id = db.Column(db.Integer, db.ForeignKey("doctor.id"), nullable = False)
    treatment = db.relationship("Treatment", backref = "appointment", uselist = False)
    
class Treatment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable = False)
    time = db.Column(db.String(50), nullable = False)
    diagnosis = db.Column(db.Text, nullable = False)
    prescription = db.Column(db.Text, nullable = False)
    notes = db.Column(db.Text)
    appointment_id = db.Column(db.Integer, db.ForeignKey("appointment.id"), unique = True, nullable = False)
    patient_id = db.Column(db.Integer, db.ForeignKey("patient.id"))
    doctor_id = db.Column(db.Integer, db.ForeignKey("doctor.id"))

    
    

