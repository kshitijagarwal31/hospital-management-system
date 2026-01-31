from flask import Flask
from application.database import db
from werkzeug.security import generate_password_hash
from application.models import Admin

def create_app():
    app = Flask(__name__)
    app.secret_key = "kshitij_hms_2025_secret"
    app.debug = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///hms.sqlite3"
    db.init_app(app)
    return app

app = create_app()
from application.controllers import * 

with app.app_context():
    db.create_all()
    existing_admin = Admin.query.filter_by(email="admin@gmail.com").first()

    if not existing_admin:
        hashed_password = generate_password_hash("123")
        user = Admin(username="admin", password=hashed_password, email="admin@gmail.com")
        db.session.add(user)
        db.session.commit()

if __name__ == "__main__":
    app.run()