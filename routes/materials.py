from flask import Blueprint, request
from extensions import db
from models import Material, User
from flask_jwt_extended import jwt_required, get_jwt_identity

material_bp = Blueprint('materials', __name__)


@material_bp.route('/classroom/<int:classroom_id>/subject/<int:subject_id>', methods=['GET'])
@jwt_required()
def get_materials(classroom_id, subject_id):
    current_user = User.query.get(get_jwt_identity())

    # The Ultimate Guard Clause
    if current_user.school_id is None:
        return {'status': 'error', 'message': 'You must be assigned to a school to access this'}, 403

    # Security: Students can only view their own classroom
    if current_user.type == 'Student' and current_user.classroom_id != classroom_id:
        return {'status': 'error', 'message': 'You do not have access to this classroom'}, 403

    # Security: Teachers can only view their own subject
    if current_user.type == 'Teacher' and current_user.subject_id != subject_id:
        return {'status': 'error', 'message': 'You do not have access to this subject'}, 403

    materials = Material.query.filter_by(classroom_id=classroom_id, subject_id=subject_id).all()
    m_list = [{"id": m.id, "title": m.title, "url": m.file_url} for m in materials]
    return {"status": "success", "materials": m_list}, 200


@material_bp.route('/create', methods=['POST'])
@jwt_required()
def create_material():
    try:
        current_user = User.query.get(get_jwt_identity())

        # The Ultimate Guard Clause
        if current_user.school_id is None:
            return {'status': 'error', 'message': 'You must be assigned to a school to access this'}, 403


        data = request.get_json()
        target_subject = data.get('subject_id')

        # Security: No students allowed
        if current_user.type == 'Student':
            return {'status': 'error', 'message': 'Students cannot create materials'}, 403

        # Security: Teachers can only post to their own subject
        if current_user.type == 'Teacher' and current_user.subject_id != target_subject:
            return {'status': 'error', 'message': 'You can only add materials to your assigned subject'}, 403

        new_mat = Material(
            title=data.get('title'),
            file_url=data.get('file_url'),
            classroom_id=data.get('classroom_id'),
            subject_id=target_subject
        )
        db.session.add(new_mat)
        db.session.commit()
        return {"status": "success", "message": "Material uploaded!"}, 201
    except Exception as e:
        db.session.rollback()
        return {"status": "error", "message": str(e)}, 400


@material_bp.route('/<int:material_id>/delete', methods=['DELETE'])
@jwt_required()
def delete_material(material_id):
    try:
        material = Material.query.get(material_id)
        if material is None:
            return {"status": "error", "message": "Material not found"}, 404

        current_user = User.query.get(get_jwt_identity())

        # The Ultimate Guard Clause
        if current_user.school_id is None:
            return {'status': 'error', 'message': 'You must be assigned to a school to access this'}, 403

        # Security Checks
        if current_user.type == 'Student':
            return {'status': 'error', 'message': 'Students cannot delete materials'}, 403
        if current_user.type == 'Teacher' and current_user.subject_id != material.subject_id:
            return {'status': 'error', 'message': 'You can only delete materials from your own subject'}, 403

        # The Delete Action
        db.session.delete(material)
        db.session.commit()
        return {"status": "success", "message": "Material deleted successfully"}, 200
    except Exception as e:
        db.session.rollback()
        return {"status": "error", "message": str(e)}, 400