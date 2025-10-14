from app import app, db, User

# Set this to the email of the user you want to promote
ADMIN_EMAIL = "seanmhart@gmail.com"

with app.app_context():
    user = User.query.filter_by(email=ADMIN_EMAIL).first()
    if user:
        user.is_admin = True
        db.session.commit()
        print(f"{ADMIN_EMAIL} is now an admin!")
    else:
        print(f"User with email {ADMIN_EMAIL} not found.")
