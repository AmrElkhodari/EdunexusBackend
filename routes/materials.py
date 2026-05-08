from flask import Blueprint, request
from extensions import db
from models import Material, User
from flask_jwt_extended import jwt_required, get_jwt_identity
import os
import uuid  # <-- NEW: Used for making unique filenames
from werkzeug.utils import secure_filename
from flask import current_app, send_from_directory

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'ppt', 'pptx', 'doc', 'docx'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


material_bp = Blueprint('materials', __name__)


@material_bp.route('/classroom/<int:classroom_id>/subject/<int:subject_id>', methods=['GET'])
@jwt_required()
def get_materials(classroom_id, subject_id):
    current_user = User.query.get(get_jwt_identity())

    if current_user.school_id is None:
        return {'status': 'error', 'message': 'You must be assigned to a school to access this'}, 403
    if current_user.type == 'Student' and current_user.classroom_id != classroom_id:
        return {'status': 'error', 'message': 'You do not have access to this classroom'}, 403
    if current_user.type == 'Teacher' and current_user.subject_id != subject_id:
        return {'status': 'error', 'message': 'You do not have access to this subject'}, 403

    materials = Material.query.filter_by(classroom_id=classroom_id, subject_id=subject_id).all()
    # Note for your Flutter developer: 'url' here is just the filename.
    # They need to call /api/materials/download/{url} to get the file.
    m_list = [{"id": m.id, "title": m.title, "url": m.file_url} for m in materials]
    return {"status": "success", "materials": m_list}, 200


@material_bp.route('/create', methods=['POST'])
@jwt_required()
def create_material():
    try:
        current_user = User.query.get(get_jwt_identity())

        title = request.form.get('title')
        classroom_id = request.form.get('classroom_id')
        subject_id = request.form.get('subject_id')

        if current_user.school_id is None:
            return {'status': 'error', 'message': 'You must be assigned to a school.'}, 403
        if current_user.type == 'Student':
            return {'status': 'error', 'message': 'Students cannot create materials'}, 403
        if current_user.type == 'Teacher' and str(current_user.subject_id) != str(subject_id):
            return {'status': 'error', 'message': 'You can only manage your assigned subject'}, 403

        if 'file' not in request.files:
            return {'status': 'error', 'message': 'No file attached to request'}, 400

        file = request.files['file']

        if file.filename == '':
            return {'status': 'error', 'message': 'No file selected'}, 400

        if file and allowed_file(file.filename):
            # 1. Sanitize the base name
            base_filename = secure_filename(file.filename)

            # 2. Add a unique UUID so files never overwrite each other!
            unique_filename = f"{uuid.uuid4().hex}_{base_filename}"

            save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(save_path)

            new_mat = Material(
                title=title,
                file_url=unique_filename,  # Save the UNIQUE name to the DB
                classroom_id=classroom_id,
                subject_id=subject_id
            )
            db.session.add(new_mat)
            db.session.commit()

            return {"status": "success", "message": "Material uploaded!", "filename": unique_filename}, 201
        else:
            return {'status': 'error', 'message': 'File type not allowed.'}, 400

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

        if current_user.school_id is None:
            return {'status': 'error', 'message': 'You must be assigned to a school'}, 403
        if current_user.type == 'Student':
            return {'status': 'error', 'message': 'Students cannot delete materials'}, 403
        if current_user.type == 'Teacher' and current_user.subject_id != material.subject_id:
            return {'status': 'error', 'message': 'You can only delete materials from your own subject'}, 403

        # NEW FIX: Delete the physical file from the hard drive!
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], material.file_url)
        if os.path.exists(file_path):
            os.remove(file_path)

        db.session.delete(material)
        db.session.commit()
        return {"status": "success", "message": "Material deleted successfully"}, 200
    except Exception as e:
        db.session.rollback()
        return {"status": "error", "message": str(e)}, 400


@material_bp.route('/download/<filename>', methods=['GET'])
@jwt_required()
def download_material(filename):
    try:
        current_user = User.query.get(get_jwt_identity())

        if current_user.school_id is None:
            return {'status': 'error', 'message': 'You must be assigned to a school to access files'}, 403

        material = Material.query.filter_by(file_url=filename).first()

        if not material:
            return {"status": "error", "message": "File record not found in database"}, 404

        if current_user.type == 'Student' and current_user.classroom_id != material.classroom_id:
            return {'status': 'error', 'message': 'This material does not belong to your classroom'}, 403
        if current_user.type == 'Teacher' and current_user.subject_id != material.subject_id:
            return {'status': 'error', 'message': 'You only have access to materials in your assigned subject'}, 403

        if current_user.type in ['Headmaster', 'Manager']:
            from models import Classroom
            classroom = Classroom.query.get(material.classroom_id)
            if classroom.school_id != current_user.school_id:
                return {'status': 'error', 'message': 'This file belongs to another school'}, 403

        return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)

    except Exception as e:
        return {"status": "error", "message": str(e)}, 400