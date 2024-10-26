from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from config import Config

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    
    from app.routes import campaign_routes, auth_routes , gemini_routes
    app.register_blueprint(campaign_routes.bp)
    app.register_blueprint(auth_routes.auth_bp)
    app.register_blueprint(gemini_routes.gemini_bp)
    
    # Create default admin account
    with app.app_context():
        db.create_all()  # Ensure all tables are created
        from app.seed import create_default_admin
        create_default_admin()
    
    return app

# run.py (can keep it the same)
from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)