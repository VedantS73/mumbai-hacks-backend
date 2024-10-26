from app import db
from datetime import datetime

class Campaign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    lower_age = db.Column(db.Integer, nullable=False)
    upper_age = db.Column(db.Integer, nullable=False)
    location = db.Column(db.JSON, nullable=False)  # Will store array as JSON
    gender = db.Column(db.String(1))
    occupation = db.Column(db.JSON, nullable=False)  # Will store array as JSON
    language = db.Column(db.JSON, nullable=False)  # Added language field
    file_name = db.Column(db.String(255))  # Added file name field
    file_path = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='draft')
    posts = db.relationship('Post', backref='campaign', lazy=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=False)

    def __init__(self, **kwargs):
        # Ensure location and occupation are lists before saving
        if 'location' in kwargs:
            if not isinstance(kwargs['location'], list):
                raise ValueError('location must be a list of strings')
            kwargs['location'] = list(map(str, kwargs['location']))
            
        if 'occupation' in kwargs:
            if not isinstance(kwargs['occupation'], list):
                raise ValueError('occupation must be a list of strings')
            kwargs['occupation'] = list(map(str, kwargs['occupation']))
            
        super(Campaign, self).__init__(**kwargs)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    ai_generated = db.Column(db.Boolean, default=True)
    status = db.Column(db.String(20), default='draft')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)