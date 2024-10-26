from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app.models.user import Admin, User
from app import db
from datetime import timedelta

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/api/auth/list', methods=['GET'])
def list():
    try:
        # Get distinct values for each field
        languages = db.session.query(User.language).distinct().all()
        genders = db.session.query(User.gender).distinct().all()
        locations = db.session.query(User.location).distinct().all()
        occupations = db.session.query(User.occupation).distinct().all()

        # Convert results from tuples to lists
        languages = [lang[0] for lang in languages if lang[0] is not None]
        genders = [gender[0] for gender in genders if gender[0] is not None]
        locations = [loc[0] for loc in locations if loc[0] is not None]
        occupations = [occ[0] for occ in occupations if occ[0] is not None]

        # Create a response object
        response = {
            'languages': languages,
            'genders': genders,
            'locations': locations,
            'occupations': occupations,
        }

        return jsonify(response), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if Admin.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 400
        
    if Admin.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already taken'}), 400
    
    admin = Admin(
        email=data['email'],
        username=data['username']
    )
    admin.set_password(data['password'])
    
    db.session.add(admin)
    db.session.commit()
    
    return jsonify({'message': 'Admin registered successfully'}), 201

@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    
    admin = Admin.query.filter_by(email=data['email']).first()
    
    if not admin or not admin.check_password(data['password']):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    access_token = create_access_token(
        identity=admin.id,
        expires_delta=timedelta(days=1)
    )
    
    return jsonify({
        'access_token': access_token,
        'admin': {
            'id': admin.id,
            'email': admin.email,
            'username': admin.username
        }
    })