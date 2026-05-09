from flask import Blueprint, request
from extensions import db
from models import User
from flask_jwt_extended import jwt_required, get_jwt_identity

admin_bp = Blueprint('admin', __name__)


# ── Helper ────────────────────────────────────────────────────
def get_admin_user():
    current_user = User.query.get(get_jwt_identity())
    if current_user.type not in ['Headmaster', 'Manager']:
        return None, ({'status': 'error', 'message': 'Unauthorized'}, 403)
    return current_user, None

def get_target_user(user_id, admin):
    if user_id == int(get_jwt_identity()):
        return None, ({'status': 'error', 'message': 'Cannot modify your own account'}, 400)
    user = User.query.get(user_id)
    if user is None:
        return None, ({'status': 'error', 'message': 'User not found'}, 404)
    if user.school_id != admin.school_id:
        return None, ({'status': 'error', 'message': 'This user does not belong to your school'}, 403)
    return user, None


# ── 1. Invite user to your school ─────────────────────────────
@admin_bp.route('/<int:user_id>/invite', methods=['PUT'])
@jwt_required()
def invite_user(user_id):
    try:
        admin, err = get_admin_user()
        if err: return err

        if user_id == int(get_jwt_identity()):
            return {'status': 'error', 'message': 'Cannot modify your own account'}, 400

        user = User.query.get(user_id)
        if user is None:
            return {'status': 'error', 'message': 'User not found'}, 404
        if user.school_id is not None:
            return {'status': 'error', 'message': 'User already belongs to a school'}, 400

        data = request.get_json()
        role = data.get('type')

        if role not in ['Student', 'Teacher', 'Manager']:
            return {'status': 'error', 'message': 'Invalid role. Choose Student, Teacher, or Manager'}, 400
        if role == 'Headmaster':
            return {'status': 'error', 'message': 'Cannot assign Headmaster role'}, 403
        if admin.type == 'Manager' and role == 'Manager':
            return {'status': 'error', 'message': 'Managers cannot assign Manager role'}, 403

        user.school_id = admin.school_id
        user.type = role

        if role == 'Student' and 'classroom_id' in data:
            user.classroom_id = data.get('classroom_id')
        if role == 'Teacher' and 'subject_id' in data:
            user.subject_id = data.get('subject_id')

        db.session.commit()
        return {'status': 'success', 'message': f'{user.first_name} invited as {role}',
                'school_id': user.school_id, 'type': user.type}, 200
    except Exception as e:
        db.session.rollback()
        return {'status': 'error', 'message': str(e)}, 400


# ── 2. Change student's classroom ─────────────────────────────
@admin_bp.route('/<int:user_id>/classroom', methods=['PUT'])
@jwt_required()
def change_classroom(user_id):
    try:
        admin, err = get_admin_user()
        if err: return err

        user, err = get_target_user(user_id, admin)
        if err: return err

        if user.type != 'Student':
            return {'status': 'error', 'message': 'User is not a Student'}, 400

        data = request.get_json()
        user.classroom_id = data.get('classroom_id')

        db.session.commit()
        return {'status': 'success', 'message': 'Classroom updated', 'classroom_id': user.classroom_id}, 200
    except Exception as e:
        db.session.rollback()
        return {'status': 'error', 'message': str(e)}, 400


# ── 3. Change teacher's subject ───────────────────────────────
@admin_bp.route('/<int:user_id>/subject', methods=['PUT'])
@jwt_required()
def change_subject(user_id):
    try:
        admin, err = get_admin_user()
        if err: return err

        user, err = get_target_user(user_id, admin)
        if err: return err

        if user.type != 'Teacher':
            return {'status': 'error', 'message': 'User is not a Teacher'}, 400

        data = request.get_json()
        user.subject_id = data.get('subject_id')

        db.session.commit()
        return {'status': 'success', 'message': 'Subject updated', 'subject_id': user.subject_id}, 200
    except Exception as e:
        db.session.rollback()
        return {'status': 'error', 'message': str(e)}, 400


# ── 4. Remove user from school ────────────────────────────────
@admin_bp.route('/<int:user_id>/remove', methods=['PUT'])
@jwt_required()
def remove_from_school(user_id):
    try:
        admin, err = get_admin_user()
        if err: return err

        user, err = get_target_user(user_id, admin)
        if err: return err

        user.school_id    = None
        user.classroom_id = None
        user.subject_id   = None
        user.type         = None

        db.session.commit()
        return {'status': 'success', 'message': f'{user.first_name} removed from school'}, 200
    except Exception as e:
        db.session.rollback()
        return {'status': 'error', 'message': str(e)}, 400


# ── 5. Delete user entirely ───────────────────────────────────
@admin_bp.route('/<int:user_id>/delete', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    try:
        admin, err = get_admin_user()
        if err: return err

        user, err = get_target_user(user_id, admin)
        if err: return err

        db.session.delete(user)
        db.session.commit()
        return {'status': 'success', 'message': 'User deleted permanently'}, 200
    except Exception as e:
        db.session.rollback()
        return {'status': 'error', 'message': str(e)}, 400