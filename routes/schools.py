from flask import Blueprint, request
from extensions import db
from models import School, User
from flask_jwt_extended import jwt_required, get_jwt_identity

school_bp = Blueprint('schools', __name__)

@school_bp.route('/create', methods=['POST'])
@jwt_required()
def create_school():
    try:
        current_user = User.query.get(get_jwt_identity())

        # Only unassigned users can create a school (they become Headmaster)
        if current_user.school_id is not None:
            return {'status': 'error', 'message': 'You already belong to a school'}, 403

        data = request.get_json()
        new_school = School(name=data.get('name'))
        db.session.add(new_school)
        db.session.flush()  # gets new_school.id before commit

        # Make the creator the Headmaster
        current_user.type = 'Headmaster'
        current_user.school_id = new_school.id

        db.session.commit()
        return {"status": "success", "message": "School created!", "school_name": new_school.name, "school_id": new_school.id}, 201
    except Exception as e:
        db.session.rollback()
        return {"status": "error", "message": str(e)}, 400

@school_bp.route('/<int:school_id>', methods = ['GET'])
def get_school(school_id):
    school = School.query.get(school_id)
    if school is None:
        return {"status": "error", "message": f"no school with id : {school_id}"}, 404
    return {"status": "success", "message": "school found successfully", "id" : school.id, "name" : school.name}, 200

@school_bp.route('/<int:school_id>/update', methods = ['PUT'])
def update_school(school_id):
    try:
        school = School.query.get(school_id)
        if school is None:
            return {"status": "error", "message": f"no school with id : {school_id}"}, 404
        data = request.get_json()
        school.name = data.get('name')
        db.session.commit()
        return {"status": "success", "message": "School updated!", "school_name": school.name}, 200
    except Exception as e:
        db.session.rollback()
        return {"status": "error", "message": str(e)}, 400

