from flask import Flask
from config import Config
from application.database import db
from application.models import Admin
from werkzeug.security import generate_password_hash


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    return app


app = create_app()
from application.controllers import * 

with app.app_context():
    db.create_all()

    existing_admin = Admin.query.filter_by(email="admin@gmail.com").first()

    if not existing_admin:
        hashed_password = generate_password_hash("Admin@123")
        admin = Admin(
            username="admin",
            password=hashed_password,
            email="admin@gmail.com"
        )
        db.session.add(admin)
        db.session.commit()


if __name__ == "__main__":
    app.run()
