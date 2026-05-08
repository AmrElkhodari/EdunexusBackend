from extensions import db
from datetime import datetime


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(20), nullable=False)
    last_name = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    type = db.Column(db.String(20), nullable=True)  # 'Student', 'Teacher', 'Headmaster', 'Manager'
    password_hash = db.Column(db.String(256), nullable=False)

    # Nullable Foreign Keys for Access Control
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'), nullable=True)
    classroom_id = db.Column(db.Integer, db.ForeignKey('classroom.id'), nullable=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=True)


class School(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)


class Classroom(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'), nullable=False)


class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject_name = db.Column(db.String(50), nullable=False)
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'), nullable=False)


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)  # db.Text is better for long messages than String(50)
    sending_time = db.Column(db.DateTime, default=datetime.utcnow)

    # Foreign Keys
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    classroom_id = db.Column(db.Integer, db.ForeignKey('classroom.id'), nullable=False)
    sent_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


class Material(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    file_url  = db.Column(db.String(200), nullable=False)  # URL to the file
    sending_time = db.Column(db.DateTime, default=datetime.utcnow)
    title = db.Column(db.String(200))

    # Foreign Keys
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    classroom_id = db.Column(db.Integer, db.ForeignKey('classroom.id'), nullable=False)


class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    title = db.Column(db.String(200))
    sending_time = db.Column(db.DateTime, default=datetime.utcnow)

    # Foreign Keys
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    classroom_id = db.Column(db.Integer, db.ForeignKey('classroom.id'), nullable=False)