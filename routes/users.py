from flask import Blueprint, request
from extensions import db
from models import User, School
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

@user_bp.route('/me', methods=['DELETE'])
@jwt_required()
def delete_account():
    try:
        from models import School, Classroom, Subject, Message, Material, Announcement
        current_user = User.query.get(get_jwt_identity())

        if current_user.type == 'Headmaster':
            school_id = current_user.school_id

            # 1. Delete all content first
            Message.query.filter_by(classroom_id=None).delete()
            Announcement.query.filter(
                Announcement.classroom_id.in_(
                    db.session.query(Classroom.id).filter_by(school_id=school_id)
                )
            ).delete(synchronize_session='fetch')

            Material.query.filter(
                Material.classroom_id.in_(
                    db.session.query(Classroom.id).filter_by(school_id=school_id)
                )
            ).delete(synchronize_session='fetch')

            Message.query.filter(
                Message.classroom_id.in_(
                    db.session.query(Classroom.id).filter_by(school_id=school_id)
                )
            ).delete(synchronize_session='fetch')

            # 2. Null out all users in the school
            User.query.filter_by(school_id=school_id).update({
                'school_id': None,
                'classroom_id': None,
                'subject_id': None,
                'type': None
            }, synchronize_session='fetch')

            # 3. Delete classrooms and subjects
            Classroom.query.filter_by(school_id=school_id).delete()
            Subject.query.filter_by(school_id=school_id).delete()

            # 4. Now safe to delete the school
            school = School.query.get(school_id)
            db.session.delete(school)

        db.session.delete(current_user)
        db.session.commit()
        return {"status": "success", "message": "Account deleted successfully"}, 200
    except Exception as e:
        db.session.rollback()
        return {"status": "error", "message": str(e)}, 400