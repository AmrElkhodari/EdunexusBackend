from flask import Blueprint, request
from extensions import db
from models import Classroom, User
from flask_jwt_extended import jwt_required, get_jwt_identity

classroom_bp = Blueprint('classrooms', __name__)


@classroom_bp.route('/', methods=['GET'])
@jwt_required()
def get_classrooms():
    current_user = User.query.get(get_jwt_identity())

    # The Ultimate Guard Clause
    if current_user.school_id is None:
        return {'status': 'error', 'message': 'You must be assigned to a school to access this'}, 403

    # Security: Students ONLY see their assigned classroom
    if current_user.type == 'Student':
        classrooms = Classroom.query.filter_by(id=current_user.classroom_id).all()

    # Security: Teachers and Admins see all classrooms in their school
    elif current_user.type in ['Teacher', 'Headmaster', 'Manager']:
        classrooms = Classroom.query.filter_by(school_id=current_user.school_id).all()

    else:
        return {'status': 'error', 'message': 'Invalid user type'}, 403

    classroom_list = [{"id": c.id, "name": c.name, "school_id": c.school_id} for c in classrooms]
    return {"status": "success", "classrooms": classroom_list}, 200


@classroom_bp.route('/create', methods=['POST'])
@jwt_required()
def create_classroom():
    try:
        current_user = User.query.get(get_jwt_identity())

        # The Ultimate Guard Clause
        if current_user.school_id is None:
            return {'status': 'error', 'message': 'You must be assigned to a school to access this'}, 403

        # Security: Only Admins can create classrooms
        if current_user.type not in ['Headmaster', 'Manager']:
            return {'status': 'error', 'message': 'Only Headmasters and Managers can create classrooms'}, 403

        data = request.get_json()
        target_school = data.get('school_id')

        # Security: Admins can only create classrooms for their OWN school
        if current_user.school_id != target_school:
            return {'status': 'error', 'message': 'You can only create classrooms for your own school'}, 403

        new_classroom = Classroom(
            name=data.get('name'),
            school_id=target_school
        )
        db.session.add(new_classroom)
        db.session.commit()
        return {"status": "success", "message": "Classroom created!", "id": new_classroom.id}, 201
    except Exception as e:
        db.session.rollback()
        return {"status": "error", "message": str(e)}, 400


@classroom_bp.route('/<int:classroom_id>/delete', methods=['DELETE'])
@jwt_required()
def delete_classroom(classroom_id):
    try:
        classroom = Classroom.query.get(classroom_id)
        if classroom is None:
            return {"status": "error", "message": "Classroom not found"}, 404

        current_user = User.query.get(get_jwt_identity())

        # The Ultimate Guard Clause
        if current_user.school_id is None:
            return {'status': 'error', 'message': 'You must be assigned to a school to access this'}, 403

        # Security: Only Admins can delete
        if current_user.type not in ['Headmaster', 'Manager']:
            return {'status': 'error', 'message': 'Only Headmasters and Managers can delete classrooms'}, 403

        # Security: Admins can only delete classrooms in their OWN school
        if current_user.school_id != classroom.school_id:
            return {'status': 'error', 'message': 'You cannot delete a classroom from another school'}, 403

        db.session.delete(classroom)
        db.session.commit()
        return {"status": "success", "message": "Classroom deleted successfully"}, 200
    except Exception as e:
        db.session.rollback()
        return {"status": "error", "message": str(e)}, 400