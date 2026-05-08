from models import Message
from extensions import db
import datetime
from extensions import socketio
from flask_socketio import join_room, leave_room, emit
from flask_jwt_extended import decode_token
from models import User

@socketio.on('send_message')
def handle_send_message(data):
    """
    Flutter triggers this when a user hits 'Send' on a chat message.
    """
    token = data.get('token')
    classroom_id = data.get('classroom_id')
    subject_id = data.get('subject_id')
    content = data.get('content')

    try:
        # 1. Scan the wristband
        decoded_token = decode_token(token)
        current_user = User.query.get(decoded_token['sub'])

        # 2. Security Check
        if current_user.type == 'Student' and current_user.classroom_id != classroom_id:
            emit('error', {'message': 'You cannot send messages to this classroom.'})
            return
        if current_user.type == 'Teacher' and current_user.subject_id != subject_id:
            emit('error', {'message': 'You cannot send messages outside your subject.'})
            return

        # 3. Save the message using YOUR exact model structure
        new_message = Message(
            content=content,
            sent_by=current_user.id,  # Updated to match your model!
            classroom_id=classroom_id,
            subject_id=subject_id
        )
        db.session.add(new_message)
        db.session.commit()

        # 4. Formulate the package (Now including the timestamp!)
        message_payload = {
            'message_id': new_message.id,
            'content': new_message.content,
            'sender_name': f"{current_user.first_name} {current_user.last_name}",
            'sender_type': current_user.type,
            'sending_time': new_message.sending_time.strftime('%Y-%m-%d %H:%M:%S')
        }

        # 5. Broadcast!
        room_name = f"chat_{classroom_id}_{subject_id}"
        emit('receive_message', message_payload, to=room_name)

        print(f"📣 {current_user.first_name} sent a message to {room_name}")

    except Exception as e:
        db.session.rollback()
        emit('error', {'message': f"Failed to send message: {str(e)}"})

@socketio.on('join_room')
def handle_join_room(data):
    token = data.get('token')
    classroom_id = data.get('classroom_id')
    subject_id = data.get('subject_id')

    decoded_token = decode_token(token)
    current_user = User.query.get(decoded_token['sub'])

    # Not in a school at all
    if current_user.school_id is None:
        emit('error', {'message': 'You must be assigned to a school.'})
        return

    # Student must belong to this classroom
    if current_user.type == 'Student' and current_user.classroom_id != int(classroom_id):
        emit('error', {'message': 'This is not your classroom.'})
        return

    # Teacher must belong to this subject
    if current_user.type == 'Teacher' and current_user.subject_id != int(subject_id):
        emit('error', {'message': 'This is not your subject.'})
        return

    room_name = f"chat_{classroom_id}_{subject_id}"
    join_room(room_name)
    print(f"✅ {current_user.first_name} joined {room_name}")