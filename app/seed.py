from app.models.user import Admin
from app import db

def create_default_admin():
    # Check if default admin exists
    if not Admin.query.filter_by(username='admin').first():
        default_admin = Admin(
            email='admin@admin.com',
            username='admin'
        )
        default_admin.set_password('admin')
        
        db.session.add(default_admin)
        try:
            db.session.commit()
            print("Default admin account created successfully!")
        except Exception as e:
            db.session.rollback()
            print(f"Error creating default admin: {str(e)}")