from flask import Blueprint, request
from extensions import db
from models import Announcement, User
from flask_jwt_extended import jwt_required, get_jwt_identity

announcement_bp = Blueprint('announcements', __name__)


@announcement_bp.route('/classroom/<int:classroom_id>/subject/<int:subject_id>', methods=['GET'])
@jwt_required()
def get_announcements(classroom_id, subject_id):
    current_user = User.query.get(get_jwt_identity())

    # The Ultimate Guard Clause
    if current_user.school_id is None:
        return {'status': 'error', 'message': 'You must be assigned to a school to access this'}, 403

    # Security: Students can only view their own assigned classroom
    if current_user.type == 'Student' and current_user.classroom_id != classroom_id:
        return {'status': 'error', 'message': 'You do not have access to this classroom'}, 403

    # Security: Teachers can only view announcements for their assigned subject
    if current_user.type == 'Teacher' and current_user.subject_id != subject_id:
        return {'status': 'error', 'message': 'You do not have access to this subject'}, 403

    # The Query: Fetch announcements strictly for this classroom AND this subject
    announcements = Announcement.query.filter_by(classroom_id=classroom_id, subject_id=subject_id).all()

    a_list = [{
        "id": a.id,
        "title": a.title,
        "content": a.content,
        "classroom_id": a.classroom_id,
        "subject_id": a.subject_id
    } for a in announcements]

    return {"status": "success", "announcements": a_list}, 200

@announcement_bp.route('/create', methods=['POST'])
@jwt_required()
def create_announcement():
    try:
        current_user = User.query.get(get_jwt_identity())

        # The Ultimate Guard Clause
        if current_user.school_id is None:
            return {'status': 'error', 'message': 'You must be assigned to a school to access this'}, 403


        data = request.get_json()
        target_classroom = data.get('classroom_id')
        target_subject = data.get('subject_id')

        # Security: No students
        if current_user.type == 'Student':
            return {'status': 'error', 'message': 'Students cannot make announcements'}, 403

        # Security: Teachers are strictly bound by their SUBJECT, not classroom
        if current_user.type == 'Teacher' and current_user.subject_id != target_subject:
            return {'status': 'error', 'message': 'You can only make announcements for your assigned subject'}, 403

        new_announcement = Announcement(
            title=data.get('title'),
            content=data.get('content'),
            classroom_id=target_classroom,
            subject_id=target_subject
        )
        db.session.add(new_announcement)
        db.session.commit()
        return {"status": "success", "message": "Announcement posted!"}, 201
    except Exception as e:
        db.session.rollback()
        return {"status": "error", "message": str(e)}, 400


@announcement_bp.route('/<int:announcement_id>/delete', methods=['DELETE'])
@jwt_required()
def delete_announcement(announcement_id):
    try:
        announcement = Announcement.query.get(announcement_id)
        if announcement is None:
            return {"status": "error", "message": "Announcement not found"}, 404

        current_user = User.query.get(get_jwt_identity())

        # The Ultimate Guard Clause
        if current_user.school_id is None:
            return {'status': 'error', 'message': 'You must be assigned to a school to access this'}, 403

        # Security Checks
        if current_user.type == 'Student':
            return {'status': 'error', 'message': 'Students cannot delete announcements'}, 403

        # Teachers can delete an announcement in ANY classroom, as long as it belongs to their subject
        if current_user.type == 'Teacher' and current_user.subject_id != announcement.subject_id:
            return {'status': 'error', 'message': 'You can only delete announcements from your own subject'}, 403

        db.session.delete(announcement)
        db.session.commit()
        return {"status": "success", "message": "Announcement deleted successfully"}, 200
    except Exception as e:
        db.session.rollback()
        return {"status": "error", "message": str(e)}, 400