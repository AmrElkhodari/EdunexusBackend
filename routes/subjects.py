from flask import Blueprint, request
from extensions import db
from models import Subject, User
from flask_jwt_extended import jwt_required, get_jwt_identity

subject_bp = Blueprint('subjects', __name__)


@subject_bp.route('/', methods=['GET'])
@jwt_required()
def get_subjects():
    current_user = User.query.get(get_jwt_identity())

    if current_user.school_id is None:
        return {'status': 'error', 'message': 'You must be assigned to a school to access this'}, 403

    # Teacher only sees their assigned subject
    if current_user.type == 'Teacher':
        subjects = Subject.query.filter_by(id=current_user.subject_id).all()

    # Everyone else sees all subjects in their school
    elif current_user.type in ['Student', 'Headmaster', 'Manager']:
        subjects = Subject.query.filter_by(school_id=current_user.school_id).all()

    else:
        return {'status': 'error', 'message': 'Invalid user type'}, 403

    subject_list = [{"id": s.id, "subject_name": s.subject_name, "school_id": s.school_id} for s in subjects]
    return {"status": "success", "subjects": subject_list}, 200


@subject_bp.route('/create', methods=['POST'])
@jwt_required()
def create_subject():
    try:
        current_user = User.query.get(get_jwt_identity())

        if current_user.school_id is None:
            return {'status': 'error', 'message': 'You must be assigned to a school to access this'}, 403

        if current_user.type not in ['Headmaster', 'Manager']:
            return {'status': 'error', 'message': 'Only Headmasters and Managers can create subjects'}, 403

        data = request.get_json()
        target_school = data.get('school_id')

        if current_user.school_id != target_school:
            return {'status': 'error', 'message': 'You can only create subjects for your own school'}, 403

        new_subject = Subject(
            subject_name=data.get('subject_name'),
            school_id=target_school
        )
        db.session.add(new_subject)
        db.session.commit()
        return {"status": "success", "message": "Subject created!", "id": new_subject.id}, 201
    except Exception as e:
        db.session.rollback()
        return {"status": "error", "message": str(e)}, 400


@subject_bp.route('/<int:subject_id>/delete', methods=['DELETE'])
@jwt_required()
def delete_subject(subject_id):
    try:
        subject = Subject.query.get(subject_id)
        if subject is None:
            return {"status": "error", "message": "Subject not found"}, 404

        current_user = User.query.get(get_jwt_identity())

        if current_user.school_id is None:
            return {'status': 'error', 'message': 'You must be assigned to a school to access this'}, 403

        if current_user.type not in ['Headmaster', 'Manager']:
            return {'status': 'error', 'message': 'Only Headmasters and Managers can delete subjects'}, 403

        if current_user.school_id != subject.school_id:
            return {'status': 'error', 'message': 'You cannot delete a subject from another school'}, 403

        db.session.delete(subject)
        db.session.commit()
        return {"status": "success", "message": "Subject deleted successfully"}, 200
    except Exception as e:
        db.session.rollback()
        return {"status": "error", "message": str(e)}, 400