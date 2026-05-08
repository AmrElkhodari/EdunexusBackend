from flask import Blueprint, request
from extensions import db
from models import Message, User
from flask_jwt_extended import jwt_required, get_jwt_identity

message_bp = Blueprint('messages', __name__)

@message_bp.route('/classroom/<int:classroom_id>/subject/<int:subject_id>', methods=['GET'])
@jwt_required()
def get_chat_history(classroom_id, subject_id):
    try:
        current_user = User.query.get(get_jwt_identity())

        # 1. The Ultimate Guard Clause
        if current_user.school_id is None:
            return {'status': 'error', 'message': 'You must be assigned to a school.'}, 403

        # 2. Security Checks
        if current_user.type == 'Student' and current_user.classroom_id != classroom_id:
            return {'status': 'error', 'message': 'Access denied to this classroom.'}, 403
        if current_user.type == 'Teacher' and current_user.subject_id != subject_id:
            return {'status': 'error', 'message': 'Access denied to this subject.'}, 403

        # 3. Fetch the last 50 messages for this specific room, newest first
        messages = Message.query.filter_by(
            classroom_id=classroom_id,
            subject_id=subject_id
        ).order_by(Message.sending_time.desc()).limit(50).all()

        # 4. Reverse the list so the oldest is at the top (how chat apps display messages)
        messages.reverse()

        # 5. Format the data to match EXACTLY what the WebSocket sends
        m_list = []
        for m in messages:
            sender = User.query.get(m.sent_by) # Grab the sender's info
            m_list.append({
                "message_id": m.id,
                "content": m.content,
                "sender_name": f"{sender.first_name} {sender.last_name}",
                "sender_type": sender.type,
                "sending_time": m.sending_time.strftime('%Y-%m-%d %H:%M:%S')
            })

        return {"status": "success", "messages": m_list}, 200

    except Exception as e:
        return {"status": "error", "message": str(e)}, 400