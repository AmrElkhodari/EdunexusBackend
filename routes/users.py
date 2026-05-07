from flask import Blueprint, request
from extensions import db
from models import User
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

user_bp = Blueprint('users', __name__)

@user_bp.route('/create', methods = ['POST'])
def create_user():
    try:
        data = request.get_json()
        password = data.get('password')  # Note: It is standard practice for the JSON key to just be 'password'
        if not password:
            return {'status': 'error', 'message': 'Password is required'}, 400
        new_user = User(
            first_name = data.get('first_name'),
            last_name = data.get('last_name'),
            email = data.get('email'),
            password_hash = generate_password_hash(data.get('password'))
        )
        db.session.add(new_user)
        db.session.commit()
        return {'status' : 'success', 'message' : 'user added', 'name' : f'{new_user.first_name} {new_user.last_name}', 'id' : new_user.id}, 201
    except Exception as e:
        db.session.rollback()
        return {'status' : 'error', 'message' : str(e)}, 400

@user_bp.route('/<int:user_id>/assign', methods = ['PUT'])
@jwt_required()
def update_user(user_id):
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        if current_user.type != 'Headmaster':
            return {'status' : 'error', 'message' : 'unauthorised user'}, 403
        user = User.query.get(user_id)
        if user is None:
            return {"status": "error", "message": f"no user with id : {user_id}"}, 404
        data = request.get_json()
        if 'first_name' in data:
            user.first_name = data.get('first_name')
        if 'last_name' in data:
            user.last_name = data.get('last_name')
        if 'email' in data:
            user.email = data.get('email')
        if 'type' in data:
            user.type = data.get('type')
        if 'school_id' in data:
            user.school_id = data.get('school_id')
        if 'classroom_id' in data:
            user.classroom_id = data.get('classroom_id')
        if 'subject_id' in data:
            user.subject_id = data.get('subject_id')
        if 'password' in data:
            user.password_hash = generate_password_hash(data.get('password'))
        db.session.commit()
        return {
            "status": "success",
            "message": "User updated!",
            'first_name' : user.first_name,
            'last_name' : user.last_name,
            'email' : user.email,
            'type' : user.type,
            'school_id' : user.school_id,
            'classroom_id' : user.classroom_id,
            'subject_id' : user.subject_id,
        }, 200
    except Exception as e:
        db.session.rollback()
        return {"status": "error", "message": str(e)}, 400

@user_bp.route('/settings', methods = ['PUT'])
@jwt_required()
def change_settings():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        data = request.get_json()
        if 'first_name' in data:
            user.first_name = data.get('first_name')
        if 'last_name' in data:
            user.last_name = data.get('last_name')
        if 'email' in data:
            user.email = data.get('email')
        if 'password' in data:
            user.password_hash = generate_password_hash(data.get('password'))
        db.session.commit()
        return {'status' : 'success', 'message' : 'settings updated successfully'}, 200
    except Exception as e:
        db.session.rollback()
        return {'status' : 'error', 'message' : str(e)}, 400

@user_bp.route('/login', methods = ['POST'])
def login_user():
    try:
        data = request.get_json()
        user = User.query.filter_by(email=data.get('email')).first()
        if user is None:
            return {'status' : 'error', 'message' : 'Invalid Email or Password'}, 401
        if not check_password_hash(user.password_hash, data.get('password')):
            return {'status': 'error', 'message': 'Invalid Email or Password'}, 401

        # The identity is the piece of data you want to remember (usually the user's ID)
        access_token = create_access_token(identity=str(user.id))
        return {
            'status': 'success',
            'message': 'Logged in successfully',
            'token' : access_token,
            'first_name' : user.first_name,
            'last_name': user.last_name,
            'type' : user.type
        }, 200
    except Exception as e:
        return {'status' : 'error', 'message' : str(e)}, 400

