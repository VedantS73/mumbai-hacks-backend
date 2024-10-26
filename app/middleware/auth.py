from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from app.models.user import Admin

def admin_required():
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            admin_id = get_jwt_identity()
            admin = Admin.query.get(admin_id)
            
            if not admin or not admin.is_active:
                return jsonify({'error': 'Admin privileges required'}), 403
                
            return fn(*args, **kwargs)
        return decorator
    return wrapper