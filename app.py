from flask import Flask
from extensions import db
import models
from routes.schools import school_bp
from routes.users import user_bp
from routes.classrooms import classroom_bp
from routes.materials import material_bp
from routes.announcements import announcement_bp
from flask_jwt_extended import JWTManager

app = Flask(__name__)

# Configure the database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///edunexus.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'super-secret-key-for-edunexus-change-later' # In a real app, this is hidden!

# Plug the db tool into this specific app
db.init_app(app)
jwt = JWTManager(app)

# Create the tables in the database
with app.app_context():
    db.create_all()

app.register_blueprint(school_bp, url_prefix = '/api/schools')
app.register_blueprint(user_bp, url_prefix = '/api/users')
app.register_blueprint(classroom_bp, url_prefix='/api/classrooms')
app.register_blueprint(material_bp, url_prefix='/api/materials')
app.register_blueprint(announcement_bp, url_prefix='/api/announcements')

@app.route('/')
def home():
    return "Hello, EduNexus! The server is alive."

@app.route('/api/status')
def api_status():
    return {"system" : "EduNexus", "Version" : "1.0", "status" : "online"}

@app.route('/api/classrooms/<classroom_id>')
def get_classroom(classroom_id):
    return {"classroom_id": classroom_id, "name": "Software Engineering", "status": "active"}

if __name__ == '__main__':
    app.run(debug=True)
