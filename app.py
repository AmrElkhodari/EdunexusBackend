from dotenv import load_dotenv
from flask import Flask
from extensions import db, socketio
import os
from routes.schools import school_bp
from routes.users import user_bp
from routes.classrooms import classroom_bp
from routes.materials import material_bp
from routes.announcements import announcement_bp
from routes.messages import message_bp
from routes.subjects import subject_bp
from routes.admin import admin_bp
from flask_jwt_extended import JWTManager
import events

load_dotenv()
app = Flask(__name__)

# Where should we save the files?
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__name__)), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Maximum file size (16 MB)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# If DATABASE_URL exists (in the cloud), use it. Otherwise, fall back to local SQLite.
# Note: Render sometimes uses 'postgres://' but SQLAlchemy requires 'postgresql://'
db_url = os.environ.get('DATABASE_URL', 'sqlite:///edunexus.db')
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET', 'fallback-secret-key')

# Plug the db tool into this specific app
db.init_app(app)
jwt = JWTManager(app)
socketio.init_app(app, cors_allowed_origins="*")

# Create the tables in the database
with app.app_context():
    db.create_all()

app.register_blueprint(school_bp, url_prefix = '/api/schools')
app.register_blueprint(user_bp, url_prefix = '/api/users')
app.register_blueprint(classroom_bp, url_prefix='/api/classrooms')
app.register_blueprint(material_bp, url_prefix='/api/materials')
app.register_blueprint(announcement_bp, url_prefix='/api/announcements')
app.register_blueprint(message_bp, url_prefix='/api/messages')
app.register_blueprint(subject_bp, url_prefix='/api/subjects')
app.register_blueprint(admin_bp, url_prefix='/api/admin')

@app.route('/')
def home():
    return "Hello, EduNexus! The server is alive."

@app.route('/api/status')
def api_status():
    return {"system" : "EduNexus", "Version" : "1.0", "status" : "online"}

if __name__ == '__main__':
    socketio.run(app, debug=True)
