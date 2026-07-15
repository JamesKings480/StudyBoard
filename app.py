from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFProtect
from datetime import date, timedelta
from config import Config
from models import db, User, Subject, Assessment, Task
from forms import RegistrationForm, LoginForm, SubjectForm, AssessmentForm, MarkForm, TaskForm
import io
import os
import pdfplumber
from docx import Document as DocxDocument
from werkzeug.utils import secure_filename

HSC_SUBJECTS = {
    'English Standard': 'https://www.nsw.gov.au/education-and-training/nesa/curriculum/english/english-standard-stage-6-2017',
    'English Advanced': 'https://www.nsw.gov.au/education-and-training/nesa/curriculum/english/english-advanced-stage-6-2017',
    'English Studies': 'https://www.nsw.gov.au/education-and-training/nesa/curriculum/english/english-studies-stage-6-2017',
    'English EAL/D': 'https://www.nsw.gov.au/education-and-training/nesa/curriculum/english/english-eald-stage-6-2017',
    'English Extension 1': 'https://www.nsw.gov.au/education-and-training/nesa/curriculum/english/english-extension-stage-6-2017',
    'English Extension 2': 'https://www.nsw.gov.au/education-and-training/nesa/curriculum/english/english-extension-stage-6-2017',
    'Mathematics Standard': 'https://www.nsw.gov.au/education-and-training/nesa/curriculum/mathematics/mathematics-standard-stage-6-2017',
    'Mathematics Advanced': 'https://www.nsw.gov.au/education-and-training/nesa/curriculum/mathematics/mathematics-advanced-stage-6-2017',
    'Mathematics Extension 1': 'https://www.nsw.gov.au/education-and-training/nesa/curriculum/mathematics/mathematics-extension-1-stage-6-2017',
    'Mathematics Extension 2': 'https://www.nsw.gov.au/education-and-training/nesa/curriculum/mathematics/mathematics-extension-2-stage-6-2017',
    'Drama': 'https://www.nsw.gov.au/education-and-training/nesa/curriculum/creative-arts/drama-stage-6-2009',
    'Business Studies': 'https://www.nsw.gov.au/education-and-training/nesa/curriculum/hsie/business-studies-stage-6-2010',
    'Economics': 'https://www.nsw.gov.au/education-and-training/nesa/curriculum/hsie/economics-stage-6-2009',
    'Geography': 'https://www.nsw.gov.au/education-and-training/nesa/curriculum/hsie/geography-stage-6-2009',
    'Aboriginal Studies': 'https://www.nsw.gov.au/education-and-training/nesa/curriculum/hsie/aboriginal-studies-stage-6-2010',
    'Ancient History': 'https://www.nsw.gov.au/education-and-training/nesa/curriculum/hsie/ancient-history-stage-6-2017',
    'Modern History': 'https://www.nsw.gov.au/education-and-training/nesa/curriculum/hsie/modern-history-stage-6-2017',
    'History Extension': 'https://www.nsw.gov.au/education-and-training/nesa/curriculum/hsie/history-extension-stage-6-2017',
    'Legal Studies': 'https://www.nsw.gov.au/education-and-training/nesa/curriculum/hsie/legal-studies-stage-6-2009',
    'French Continuers': 'https://www.nsw.gov.au/education-and-training/nesa/curriculum/languages/french-stage-6-2009',
    'Chinese Continuers': 'https://www.nsw.gov.au/education-and-training/nesa/curriculum/languages/chinese-stage-6-2009',
    'Latin Continuers': 'https://www.nsw.gov.au/education-and-training/nesa/curriculum/languages/latin-stage-6-2010',
    'Modern Greek Beginners': 'https://www.nsw.gov.au/education-and-training/nesa/curriculum/languages/modern-greek-stage-6-2009',
    'Music 1': 'https://www.nsw.gov.au/education-and-training/nesa/curriculum/creative-arts/music-stage-6-2009',
    'Music 2': 'https://www.nsw.gov.au/education-and-training/nesa/curriculum/creative-arts/music-stage-6-2009',
    'Music Extension': 'https://www.nsw.gov.au/education-and-training/nesa/curriculum/creative-arts/music-extension-stage-6-2009',
    'Health and Movement Science': 'https://www.nsw.gov.au/education-and-training/nesa/curriculum/pdhpe/health-and-movement-science-stage-6-2024',
    'Studies of Religion I': 'https://www.nsw.gov.au/education-and-training/nesa/curriculum/hsie/studies-of-religion-stage-6-2009',
    'Studies of Religion II': 'https://www.nsw.gov.au/education-and-training/nesa/curriculum/hsie/studies-of-religion-stage-6-2009',
    'Biology': 'https://www.nsw.gov.au/education-and-training/nesa/curriculum/science/biology-stage-6-2017',
    'Chemistry': 'https://www.nsw.gov.au/education-and-training/nesa/curriculum/science/chemistry-stage-6-2017',
    'Earth and Environmental Science': 'https://www.nsw.gov.au/education-and-training/nesa/curriculum/science/earth-and-environmental-science-stage-6-2017',
    'Physics': 'https://www.nsw.gov.au/education-and-training/nesa/curriculum/science/physics-stage-6-2017',
    'Science Extension': 'https://www.nsw.gov.au/education-and-training/nesa/curriculum/science/science-extension-stage-6-2017',
    'Design and Technology': 'https://www.nsw.gov.au/education-and-training/nesa/curriculum/tas/design-and-technology-stage-6-2018',
    'Engineering Studies': 'https://www.nsw.gov.au/education-and-training/nesa/curriculum/tas/engineering-studies-stage-6-2022',
    'Industrial Technology': 'https://www.nsw.gov.au/education-and-training/nesa/curriculum/tas/industrial-technology-stage-6-2019',
    'Software Engineering': 'https://www.nsw.gov.au/education-and-training/nesa/curriculum/tas/software-engineering-11-12-2022',
    'Visual Arts': 'https://www.nsw.gov.au/education-and-training/nesa/curriculum/creative-arts/visual-arts-stage-6-2016',
}

from models import db, User, Subject, Assessment, Task, StudySession
from forms import RegistrationForm, LoginForm, SubjectForm, AssessmentForm, MarkForm, TaskForm

app = Flask(__name__)
app.config.from_object(Config)
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}
MAX_NOTIFICATION_CHARS = 20000
MAX_FILE_SIZE = 5 * 1024 * 1024 

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_file(uploaded_file, filename):
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    text = ''
    try:
        uploaded_file.seek(0)
        file_bytes = io.BytesIO(uploaded_file.read())
        if ext == 'pdf':
            with pdfplumber.open(file_bytes) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + '\n'
        elif ext == 'docx':
            document = DocxDocument(file_bytes)
            for para in document.paragraphs:
                text += para.text + '\n'
            for table in document.tables:
                for row in table.rows:
                    for cell in row.cells:
                        if cell.text.strip():
                            text += cell.text.strip() + '\n'
        elif ext == 'txt':
            text = file_bytes.read().decode('utf-8', errors='ignore')
    except Exception as error:
        print('EXTRACTION ERROR [' + ext + ']:', error)
        return ''
    return text.strip()


def get_notification_text(form):
    typed_text = form.task_notification.data.strip() if form.task_notification.data else ''

    uploaded_file = request.files.get('task_file')
    if not uploaded_file or not uploaded_file.filename:
        return typed_text, None

    if uploaded_file.filename.lower().endswith('.doc'):
        return typed_text, 'Old .doc files cannot be read. Open it in Word, save it as .docx, then upload again.'

    if not allowed_file(uploaded_file.filename):
        return typed_text, 'Only PDF, Word (.docx) and text files are allowed.'

    uploaded_file.seek(0, os.SEEK_END)
    file_size = uploaded_file.tell()
    uploaded_file.seek(0)
    if file_size > MAX_FILE_SIZE:
        return typed_text, 'File is too large. Maximum size is 5MB.'

    filename = secure_filename(uploaded_file.filename)
    extracted = extract_text_from_file(uploaded_file, filename)
    if not extracted:
        return typed_text, 'Could not read any text from that file. It may be a scan rather than real text. Try another file or type the task in.'

    return extracted[:MAX_NOTIFICATION_CHARS], None

csrf = CSRFProtect(app)
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response


@app.context_processor
def inject_sidebar_subjects():
    if current_user.is_authenticated:
        subjects = Subject.query.filter_by(user_id=current_user.id).order_by(Subject.name).all()
        return dict(sidebar_subjects=subjects)
    return dict(sidebar_subjects=[])


@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = RegistrationForm()
    if form.validate_on_submit():
        existing = User.query.filter_by(email=form.email.data.lower().strip()).first()
        if existing:
            flash('Unable to create account. Please try a different email.', 'danger')
            return redirect(url_for('register'))
        user = User(email=form.email.data.lower().strip())
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid email or password.', 'danger')
            return redirect(url_for('login'))
        login_user(user)
        return redirect(url_for('dashboard'))
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)

    subjects = Subject.query.filter_by(user_id=current_user.id).all()
    upcoming_assessments = Assessment.query.join(Subject).filter(
        Subject.user_id == current_user.id,
        Assessment.due_date >= today,
        Assessment.status != 'Completed'
    ).order_by(Assessment.due_date).limit(10).all()
    todays_tasks = Task.query.join(Assessment).join(Subject).filter(
        Subject.user_id == current_user.id,
        Task.scheduled_date <= today,
        Task.status == 'Incomplete'
    ).order_by(Task.scheduled_date).all()

    sessions = StudySession.query.filter(
        StudySession.user_id == current_user.id,
        StudySession.date >= start_of_week,
        StudySession.date <= end_of_week
    ).all()
    total_weekly_minutes = sum(s.duration_minutes for s in sessions)
    total_seconds = int(total_weekly_minutes * 60)
    if total_seconds >= 3600:
        weekly_display = str(total_seconds // 3600) + 'h ' + str((total_seconds % 3600) // 60) + 'm'
    elif total_seconds >= 60:
        weekly_display = str(total_seconds // 60) + 'm ' + str(total_seconds % 60) + 's'
    else:
        weekly_display = str(total_seconds) + 's'

    daily_totals = [0] * 7
    for s in sessions:
        day_index = (s.date - start_of_week).days
        if 0 <= day_index < 7:
            daily_totals[day_index] += s.duration_minutes
    max_daily = max(daily_totals) if max(daily_totals) > 0 else 1

    day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    return render_template('dashboard.html', subjects=subjects, upcoming_assessments=upcoming_assessments, todays_tasks=todays_tasks, total_weekly_minutes=total_weekly_minutes, weekly_display=weekly_display, daily_totals=daily_totals, max_daily=max_daily, day_names=day_names, today=today)

@app.route('/study/save', methods=['POST'])
@login_required
def save_study_session():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid data'}), 400
    subject_id = data.get('subject_id')
    duration = data.get('duration_minutes', 0)

    subject = Subject.query.get(subject_id)
    if not subject or subject.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403

    session = StudySession(
        duration_minutes=round(duration, 2),
        date=date.today(),
        subject_id=subject_id,
        user_id=current_user.id
    )
    db.session.add(session)
    db.session.commit()
    return jsonify({'success': True, 'duration': session.duration_minutes})

@app.route('/subjects')
@login_required
def subjects_list():
    subjects = Subject.query.filter_by(user_id=current_user.id).order_by(Subject.name).all()
    return render_template('subjects.html', subjects=subjects)

@app.route('/subject/new', methods=['GET', 'POST'])
@login_required
def create_subject():
    form = SubjectForm()
    form.name.choices = [(s, s) for s in HSC_SUBJECTS.keys()]
    if form.validate_on_submit():
        subject = Subject(
            name=form.name.data,
            colour=form.colour.data or '#4A90D9',
            year_level=form.year_level.data,
            nesa_url=HSC_SUBJECTS.get(form.name.data),
            user_id=current_user.id
        )
        db.session.add(subject)
        db.session.commit()
        flash(f'Subject "{subject.name}" created successfully!', 'success')
        return redirect(url_for('subject_detail', subject_id=subject.id))
    return render_template('subject_form.html', form=form, title='Add New Subject')

@app.route('/subject/<int:subject_id>')
@login_required
def subject_detail(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    if subject.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    assessments = Assessment.query.filter_by(subject_id=subject.id).order_by(Assessment.due_date).all()
    return render_template('subject_detail.html', subject=subject, assessments=assessments, today=date.today())

@app.route('/subject/<int:subject_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    if subject.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    form = SubjectForm(obj=subject)
    form.name.choices = [(s, s) for s in HSC_SUBJECTS.keys()]
    if form.validate_on_submit():
        subject.name = form.name.data
        subject.colour = form.colour.data or '#4A90D9'
        subject.year_level = form.year_level.data
        subject.nesa_url = HSC_SUBJECTS.get(form.name.data)
        db.session.commit()
        flash(f'Subject "{subject.name}" updated!', 'success')
        return redirect(url_for('subject_detail', subject_id=subject.id))
    return render_template('subject_form.html', form=form, title='Edit Subject')


@app.route('/subject/<int:subject_id>/delete', methods=['POST'])
@login_required
def delete_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    if subject.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    name = subject.name
    db.session.delete(subject)
    db.session.commit()
    flash(f'Subject "{name}" deleted.', 'info')
    return redirect(url_for('subjects_list'))

@app.route('/subject/<int:subject_id>/assessment/new', methods=['GET', 'POST'])
@login_required
def create_assessment(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    if subject.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    form = AssessmentForm()
    if form.validate_on_submit():
        notification_text, upload_error = get_notification_text(form)
        if upload_error:
            flash(upload_error, 'danger')
            return render_template('assessment_form.html', form=form, subject=subject, title='New Assessment')

        assessment = Assessment(
            name=form.name.data.strip(),
            due_date=form.due_date.data,
            weighting=form.weighting.data,
            assessment_type=form.assessment_type.data,
            task_notification=notification_text,
            subject_id=subject.id
        )
        db.session.add(assessment)
        db.session.commit()
        flash(f'Assessment "{assessment.name}" created!', 'success')
        return redirect(url_for('assessment_detail', assessment_id=assessment.id))
    return render_template('assessment_form.html', form=form, subject=subject, title='New Assessment')

@app.route('/assessment/<int:assessment_id>')
@login_required
def assessment_detail(assessment_id):
    assessment = Assessment.query.get_or_404(assessment_id)
    subject = assessment.subject
    if subject.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    tasks = Task.query.filter_by(assessment_id=assessment.id).order_by(Task.scheduled_date).all()
    mark_form = MarkForm()
    return render_template('assessment_detail.html', assessment=assessment, subject=subject, tasks=tasks, mark_form=mark_form, today=date.today())

@app.route('/assessment/<int:assessment_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_assessment(assessment_id):
    assessment = Assessment.query.get_or_404(assessment_id)
    subject = assessment.subject
    if subject.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    form = AssessmentForm(obj=assessment)
    if form.validate_on_submit():
        notification_text, upload_error = get_notification_text(form)
        if upload_error:
            flash(upload_error, 'danger')
            return render_template('assessment_form.html', form=form, subject=subject, title='Edit Assessment')

        assessment.name = form.name.data.strip()
        assessment.due_date = form.due_date.data
        assessment.weighting = form.weighting.data
        assessment.assessment_type = form.assessment_type.data
        assessment.task_notification = notification_text
        db.session.commit()
        flash(f'Assessment "{assessment.name}" updated!', 'success')
        return redirect(url_for('assessment_detail', assessment_id=assessment.id))
    return render_template('assessment_form.html', form=form, subject=subject, title='Edit Assessment')


@app.route('/assessment/<int:assessment_id>/delete', methods=['POST'])
@login_required
def delete_assessment(assessment_id):
    assessment = Assessment.query.get_or_404(assessment_id)
    subject = assessment.subject
    if subject.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    subject_id = subject.id
    db.session.delete(assessment)
    db.session.commit()
    flash('Assessment deleted.', 'info')
    return redirect(url_for('subject_detail', subject_id=subject_id))

@app.route('/assessment/<int:assessment_id>/mark', methods=['POST'])
@login_required
def save_mark(assessment_id):
    assessment = Assessment.query.get_or_404(assessment_id)
    if assessment.subject.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    form = MarkForm()
    if form.validate_on_submit():
        assessment.mark = form.mark.data
        assessment.status = 'Completed'
        db.session.commit()
        flash(f'Mark saved: {assessment.mark}%', 'success')
    return redirect(url_for('assessment_detail', assessment_id=assessment.id))



@app.route('/task/<int:task_id>/toggle', methods=['POST'])
@login_required
def toggle_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.assessment.subject.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    task.status = 'Complete' if task.status == 'Incomplete' else 'Incomplete'
    db.session.commit()
    return redirect(request.referrer or url_for('dashboard'))


@app.route('/assessment/<int:assessment_id>/task/new', methods=['POST'])
@login_required
def add_task(assessment_id):
    assessment = Assessment.query.get_or_404(assessment_id)
    if assessment.subject.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    form = TaskForm()
    if form.validate_on_submit():
        task = Task(
            title=form.title.data.strip(),
            scheduled_date=form.scheduled_date.data,
            assessment_id=assessment.id
        )
        db.session.add(task)
        db.session.commit()
        flash('Task added!', 'success')
    return redirect(url_for('assessment_detail', assessment_id=assessment.id))

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, port=5000)