from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    study_sessions = db.relationship('StudySession', backref='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Subject(db.Model):
    __tablename__ = 'subjects'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    colour = db.Column(db.String(7), nullable=False, default='#4A90D9')
    year_level = db.Column(db.String(20), nullable=False, default='Year 12')
    nesa_url = db.Column(db.String(300), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    assessments = db.relationship('Assessment', backref='subject', lazy=True, cascade='all, delete-orphan')
    study_sessions = db.relationship('StudySession', backref='subject', lazy=True, cascade='all, delete-orphan')

class Assessment(db.Model):
    __tablename__ = 'assessments'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    weighting = db.Column(db.Float, nullable=False)
    assessment_type = db.Column(db.String(50), nullable=False, default='Assignment')
    status = db.Column(db.String(20), nullable=False, default='Upcoming')
    mark = db.Column(db.Float, nullable=True)
    task_notification = db.Column(db.Text, nullable=True)
    task_file_name = db.Column(db.String(255), nullable=True)
    task_file_size = db.Column(db.Integer, nullable=True)
    task_file_data = db.Column(db.LargeBinary, nullable=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    tasks = db.relationship('Task', backref='assessment', lazy=True, cascade='all, delete-orphan')

    @property
    def task_file_icon(self):
        if not self.task_file_name:
            return ''
        ext = self.task_file_name.rsplit('.', 1)[-1].lower()
        if ext == 'pdf':
            return 'bi-file-earmark-pdf'
        if ext == 'docx':
            return 'bi-file-earmark-word'
        return 'bi-file-earmark-text'

    @property
    def task_file_size_text(self):
        if not self.task_file_size:
            return ''
        kb = self.task_file_size / 1024
        if kb > 1024:
            return str(round(kb / 1024, 1)) + ' MB'
        return str(round(kb)) + ' KB'

class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    scheduled_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Incomplete')
    assessment_id = db.Column(db.Integer, db.ForeignKey('assessments.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
class StudySession(db.Model):
    __tablename__ = 'study_sessions'
    id = db.Column(db.Integer, primary_key=True)
    duration_minutes = db.Column(db.Float, nullable=False, default=0)
    date = db.Column(db.Date, nullable=False, default=date.today)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)