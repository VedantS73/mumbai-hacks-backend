import os, json
from flask import Blueprint, request, jsonify, current_app, send_from_directory
from werkzeug.utils import secure_filename
from app.models.campaign import *
from app.models.user import *
from app.services.campaign_services import CampaignService
from app.services.ai_service import AIService
from app import db
from app.middleware.auth import admin_required
from flask_jwt_extended import get_jwt_identity

bp = Blueprint('campaigns', __name__)

class Config:
    UPLOAD_FOLDER = 'uploads/campaigns'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

@bp.route('/api/campaigns/target', methods=['GET'])
def get_target_audience_number():
    data = request.args.to_dict()  # Use request.args for GET requests

    # Try to parse JSON fields, if necessary
    try:
        # For locations, occupations, and languages, expect them to be JSON strings
        data['location'] = json.loads(data.get('location', '[]'))
        data['occupation'] = json.loads(data.get('occupation', '[]'))
        data['language'] = json.loads(data.get('language', '[]'))
    except json.JSONDecodeError:
        return jsonify({'error': 'Invalid JSON format for location, language, or occupation'}), 400

    # Validate required fields
    required_fields = ['lower_age', 'upper_age', 'location', 'occupation', 'language']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400

    # Query the User model for matching users
    query = User.query

    # Filtering based on the provided parameters
    if 'lower_age' in data:
        query = query.filter(User.age >= int(data['lower_age']))
    if 'upper_age' in data:
        query = query.filter(User.age <= int(data['upper_age']))
    if 'location' in data and data['location']:
        query = query.filter(User.location.in_(data['location']))
    if 'occupation' in data and data['occupation']:
        query = query.filter(User.occupation.in_(data['occupation']))
    if 'language' in data and data['language']:
        query = query.filter(User.language.in_(data['language']))
    
    # Count the matching users
    matching_users_count = query.count()

    return jsonify({
        'matching_users_count': matching_users_count
    }), 200

@bp.route('/api/campaigns', methods=['POST'])
@admin_required()
def create_campaign():
    admin_id = get_jwt_identity()
    
    filename = None
    file_path = None
    
    try:
        # Validate form data
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
            
        # Get the image file
        image = request.files['image']
        if image.filename == '':
            return jsonify({'error': 'No selected file'}), 400
            
        # Get other form data
        data = request.form.to_dict()
        
        # Parse JSON strings back to lists
        try:
            # Parse JSON strings to lists if they are strings
            data['location'] = json.loads(data.get('location', '[]')) if isinstance(data.get('location'), str) else data.get('location')
            data['occupation'] = json.loads(data.get('occupation', '[]')) if isinstance(data.get('occupation'), str) else data.get('occupation')
            data['language'] = json.loads(data.get('language', '[]')) if isinstance(data.get('language'), str) else data.get('language')

            print("Raw data:", data)
            print("Location (before parsing):", data.get('location'))
            print("Occupation (before parsing):", data.get('occupation'))
            print("Language (before parsing):", data.get('language'))

        except json.JSONDecodeError:
            return jsonify({'error': 'Invalid JSON format for location, language, or occupation'}), 400
        
        # Validate required fields
        required_fields = ['name', 'lower_age', 'upper_age', 'location', 'occupation', 'language', 'title', 'description']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        # Handle image upload
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            
            # Create upload directory if it doesn't exist
            upload_dir = os.path.join(current_app.root_path, Config.UPLOAD_FOLDER)
            os.makedirs(upload_dir, exist_ok=True)
            
            # Generate unique filename
            base, ext = os.path.splitext(filename)
            counter = 1
            while os.path.exists(os.path.join(upload_dir, filename)):
                filename = f"{base}_{counter}{ext}"
                counter += 1
            
            # Save the file
            file_path = os.path.join(upload_dir, filename)
            image.save(file_path)
            
            # Create campaign with image info
            campaign = Campaign(
                name=data['name'],
                lower_age=int(data['lower_age']),
                upper_age=int(data['upper_age']),
                location=data['location'],
                gender=data.get('gender'),
                occupation=data['occupation'],
                language=data['language'],
                file_name=filename,
                file_path=file_path,
                admin_id=admin_id,
                status='draft',
                title=data.get('title', ''),
                description=data.get('description', '')
            )
            
            db.session.add(campaign)
            db.session.commit()

            # If you want to create or update the user fields, check if the user exists first
            user = User.query.filter_by(id=admin_id).first()
            if user:
                user.gender = data.get('gender', user.gender)
                user.location = ','.join(data['location'])  # Convert list to comma-separated string
                user.occupation = ','.join(data['occupation'])  # Convert list to comma-separated string
                user.ig_handle = data.get('ig_handle', user.ig_handle)
                user.fb_handle = data.get('fb_handle', user.fb_handle)
                user.twitter_handle = data.get('twitter_handle', user.twitter_handle)

                db.session.commit()

            matching_users = CampaignService.get_matching_users_count(campaign)
            
            return jsonify({
                'id': campaign.id,
                'matching_users': matching_users,
                'message': 'Campaign created successfully',
                'file_name': filename
            }), 201
        else:
            return jsonify({'error': 'Invalid file type'}), 400
            
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({'error': f'Failed to create campaign: {str(e)}'}), 500


    
@bp.route('/api/campaigns/images/<filename>', methods=['GET'])
def get_campaign_image(filename):
    """Fetch an uploaded campaign image by filename."""
    try:
        # Define the full path to the uploads directory
        upload_dir = os.path.join(current_app.root_path, Config.UPLOAD_FOLDER)
        
        # Serve the file from the upload directory
        return send_from_directory(upload_dir, filename)
    except FileNotFoundError:
        return jsonify({'error': 'Image not found'}), 404
    except Exception as e:
        return jsonify({'error': f'Failed to retrieve image: {str(e)}'}), 500

@bp.route('/api/campaigns', methods=['GET'])
@admin_required()
def get_admin_campaigns():
    admin_id = get_jwt_identity()
    campaigns = Campaign.query.filter_by(admin_id=admin_id).all()
    
    return jsonify([{
        'id': c.id,
        'name': c.name,
        'status': c.status,
        'location': c.location,
        'occupation': c.occupation,
        'language': c.language,
        'file_name': c.file_name,
        'file_url': f'/api/campaigns/images/{c.file_name}' if c.file_name else None,
        'created_at': c.created_at.isoformat()
    } for c in campaigns]), 200



@bp.route('/api/campaigns/<int:campaign_id>/generate-post', methods=['POST'])
@admin_required()
def generate_post(campaign_id):
    try:
        campaign = Campaign.query.get_or_404(campaign_id)
        
        # Generate post using AI service
        content = AIService.generate_post(campaign)
        
        post = Post(
            campaign_id=campaign_id,
            content=content,
            ai_generated=True
        )
        
        db.session.add(post)
        db.session.commit()
        
        return jsonify({
            'id': post.id,
            'content': content,
            'message': 'Post generated successfully'
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to generate post: {str(e)}'}), 500