from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import deferred
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


def file_icon_for(filename):
    ext = filename.rsplit('.', 1)[-1].lower() if filename and '.' in filename else ''
    if ext == 'pdf':
        return 'bi-file-earmark-pdf'
    if ext in ('docx', 'doc'):
        return 'bi-file-earmark-word'
    if ext == 'pptx':
        return 'bi-file-earmark-slides'
    if ext in ('png', 'jpg', 'jpeg'):
        return 'bi-file-earmark-image'
    return 'bi-file-earmark-text'


def size_text_for(size_bytes):
    if not size_bytes:
        return ''
    kb = size_bytes / 1024
    if kb > 1024:
        return str(round(kb / 1024, 1)) + ' MB'
    return str(round(kb)) + ' KB'


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
    todo_items = db.relationship('TodoItem', backref='subject', lazy=True, cascade='all, delete-orphan')
    files = db.relationship('SubjectFile', backref='subject', lazy=True,
                            cascade='all, delete-orphan',
                            order_by='desc(SubjectFile.created_at)')

    topics = db.relationship('Topic', backref='subject', lazy=True, cascade='all, delete-orphan')

    @property
    def flashcards(self):
        return Flashcard.query.join(Topic).filter(Topic.subject_id == self.id).all()

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
    task_file_data = deferred(db.Column(db.LargeBinary, nullable=True))
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    tasks = db.relationship('Task', backref='assessment', lazy=True, cascade='all, delete-orphan')

    @property
    def task_file_icon(self):
        return file_icon_for(self.task_file_name) if self.task_file_name else ''

    @property
    def task_file_size_text(self):
        return size_text_for(self.task_file_size)

class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    scheduled_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Incomplete')
    assessment_id = db.Column(db.Integer, db.ForeignKey('assessments.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def is_todo(self):
        return False

    @property
    def subject(self):
        return self.assessment.subject

    @property
    def context_label(self):
        return self.assessment.name
    
class SubjectFile(db.Model):
    __tablename__ = 'subject_files'
    id = db.Column(db.Integer, primary_key=True)
    file_name = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    file_data = deferred(db.Column(db.LargeBinary, nullable=False))
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def icon(self):
        return file_icon_for(self.file_name)

    @property
    def size_text(self):
        return size_text_for(self.file_size)


class TodoItem(db.Model):
    __tablename__ = 'todo_items'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    scheduled_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Incomplete')
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def is_todo(self):
        return True

    @property
    def context_label(self):
        return 'To-do'


class StudySession(db.Model):
    __tablename__ = 'study_sessions'
    id = db.Column(db.Integer, primary_key=True)
    duration_minutes = db.Column(db.Float, nullable=False, default=0)
    date = db.Column(db.Date, nullable=False, default=date.today)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Topic(db.Model):
    __tablename__ = 'topics'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    flashcards = db.relationship('Flashcard', backref='topic', lazy=True,
                                 cascade='all, delete-orphan')

    __table_args__ = (
        db.UniqueConstraint('subject_id', 'name', name='uq_topic_name_per_subject'),
    )


class Flashcard(db.Model):
    __tablename__ = 'flashcards'
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey('topics.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviews = db.relationship('FlashcardReview', backref='flashcard', lazy=True,
                              cascade='all, delete-orphan')

    @property
    def subject(self):
        return self.topic.subject


class FlashcardReview(db.Model):
    __tablename__ = 'flashcard_reviews'
    id = db.Column(db.Integer, primary_key=True)
    was_correct = db.Column(db.Boolean, nullable=False)
    reviewed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    flashcard_id = db.Column(db.Integer, db.ForeignKey('flashcards.id'), nullable=False)