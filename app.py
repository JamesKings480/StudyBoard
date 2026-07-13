from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFProtect
from datetime import date
from config import Config
from models import db, User, Subject, Assessment, Task
from forms import RegistrationForm, LoginForm, SubjectForm
HSC_SUBJECTS = {
    'English Studies': 'http://insites.newington.nsw.edu.au/academicguide-year11-12/hsc/hsc-subjects/english-studies/',
    'English EAL/D': 'http://insites.newington.nsw.edu.au/academicguide-year11-12/hsc/hsc-subjects/english-eald/',
    'English (Standard)': 'http://insites.newington.nsw.edu.au/academicguide-year11-12/hsc/hsc-subjects/english-standard/',
    'English (Advanced)': 'http://insites.newington.nsw.edu.au/academicguide-year11-12/hsc/hsc-subjects/english-advanced/',
    'English Extension 1': 'http://insites.newington.nsw.edu.au/academicguide-year11-12/hsc/hsc-subjects/english-extension-courses/',
    'English Extension 2': 'https://insites.newington.nsw.edu.au/academicguide-year11-12/hsc/hsc-subjects/english-extension-2-year-12/',
    'Mathematics Standard': 'https://insites.newington.nsw.edu.au/academicguide-year11-12/hsc/hsc-subjects/mathematics-standard/',
    'Mathematics Advanced': 'https://insites.newington.nsw.edu.au/academicguide-year11-12/hsc/hsc-subjects/mathematics-advanced/',
    'Mathematics Extension 1': 'https://insites.newington.nsw.edu.au/academicguide-year11-12/hsc/hsc-subjects/mathematics-extension-1/',
    'Mathematics Extension 2': 'https://insites.newington.nsw.edu.au/academicguide-year11-12/hsc/hsc-subjects/mathematics-extension-2/',
    'Drama': 'http://insites.newington.nsw.edu.au/academicguide-year11-12/hsc/hsc-subjects/drama-2-unit/',
    'Entertainment (VET)': 'https://insites.newington.nsw.edu.au/academicguide-year11-12/hsc/hsc-subjects/vet-entertainment-course/',
    'Business Services (VET)': 'http://insites.newington.nsw.edu.au/academicguide-year11-12/hsc/hsc-subjects/business-services-vet/',
    'Business Studies': 'http://insites.newington.nsw.edu.au/academicguide-year11-12/hsc/hsc-subjects/business-studies/',
    'Economics': 'http://insites.newington.nsw.edu.au/academicguide-year11-12/hsc/hsc-subjects/economics/',
    'Geography': 'http://insites.newington.nsw.edu.au/academicguide-year11-12/hsc/hsc-subjects/geography/',
    'Aboriginal Studies': 'https://insites.newington.nsw.edu.au/academicguide-year11-12/hsc/hsc-subjects/aboriginal-studies/',
    'Ancient History': 'http://insites.newington.nsw.edu.au/academicguide-year11-12/hsc/hsc-subjects/ancient-history/',
    'History Extension': 'http://insites.newington.nsw.edu.au/academicguide-year11-12/hsc/hsc-subjects/history-extension/',
    'Legal Studies': 'http://insites.newington.nsw.edu.au/academicguide-year11-12/hsc/hsc-subjects/legal-studies/',
    'Modern History': 'http://insites.newington.nsw.edu.au/academicguide-year11-12/hsc/hsc-subjects/modern-history/',
    'External Language Courses': 'http://insites.newington.nsw.edu.au/academicguide-year11-12/hsc/hsc-subjects/languages-external-language-study/',
    'French Continuers': 'http://insites.newington.nsw.edu.au/academicguide-year11-12/hsc/hsc-subjects/french-continuers/',
    'Chinese Continuers': 'http://insites.newington.nsw.edu.au/academicguide-year11-12/hsc/hsc-subjects/chinese-continuers/',
    'Latin Continuers': 'http://insites.newington.nsw.edu.au/academicguide-year11-12/hsc/hsc-subjects/latin-continuers/',
    'Modern Greek Beginners': 'http://insites.newington.nsw.edu.au/academicguide-year11-12/hsc/hsc-subjects/modern-greek-beginners/',
    'Music 1': 'http://insites.newington.nsw.edu.au/academicguide-year11-12/hsc/hsc-subjects/music-1/',
    'Music 2': 'http://insites.newington.nsw.edu.au/academicguide-year11-12/hsc/hsc-subjects/music-2/',
    'Music Extension': 'http://insites.newington.nsw.edu.au/academicguide-year11-12/hsc/hsc-subjects/music-extension/',
    'Health and Movement Science': 'http://insites.newington.nsw.edu.au/academicguide-year11-12/hsc/hsc-subjects/personal-development-health-and-physical-education/',
    'Studies of Religion I': 'http://insites.newington.nsw.edu.au/academicguide-year11-12/hsc/hsc-subjects/studies-of-religion-i/',
    'Studies of Religion II': 'http://insites.newington.nsw.edu.au/academicguide-year11-12/hsc/hsc-subjects/studies-of-religion-ii/',
    'Biology': 'http://insites.newington.nsw.edu.au/academicguide-year11-12/hsc/hsc-subjects/biology/',
    'Chemistry': 'http://insites.newington.nsw.edu.au/academicguide-year11-12/hsc/hsc-subjects/chemistry/',
    'Earth and Environmental Science': 'http://insites.newington.nsw.edu.au/academicguide-year11-12/hsc/hsc-subjects/earth-and-environmental-science/',
    'Physics': 'http://insites.newington.nsw.edu.au/academicguide-year11-12/hsc/hsc-subjects/physics/',
    'Science Extension': 'https://insites.newington.nsw.edu.au/academicguide-year11-12/hsc/hsc-subjects/year-12-hsc-science-extension/',
    'Construction (VET)': 'http://insites.newington.nsw.edu.au/academicguide-year11-12/hsc/hsc-subjects/construction-vet/',
    'Design and Technology': 'http://insites.newington.nsw.edu.au/academicguide-year11-12/hsc/hsc-subjects/design-and-technology/',
    'Engineering Studies': 'http://insites.newington.nsw.edu.au/academicguide-year11-12/hsc/hsc-subjects/engineering-studies/',
    'Hospitality (VET)': 'http://insites.newington.nsw.edu.au/academicguide-year11-12/hsc/hsc-subjects/hospitality-vet/',
    'Industrial Technology': 'http://insites.newington.nsw.edu.au/academicguide-year11-12/hsc/hsc-subjects/industrial-technology/',
    'Software Engineering': 'https://insites.newington.nsw.edu.au/academicguide-year11-12/hsc/hsc-subjects/software-engineering/',
    'Visual Arts': 'http://insites.newington.nsw.edu.au/academicguide-year11-12/hsc/hsc-subjects/visual-arts/',
}


app = Flask(__name__)
app.config.from_object(Config)

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
    subjects = Subject.query.filter_by(user_id=current_user.id).all()
    upcoming_assessments = Assessment.query.join(Subject).filter(Subject.user_id == current_user.id, Assessment.due_date >= today, Assessment.status != 'Completed').order_by(Assessment.due_date).limit(10).all()
    todays_tasks = Task.query.join(Assessment).join(Subject).filter(Subject.user_id == current_user.id, Task.scheduled_date <= today, Task.status == 'Incomplete').order_by(Task.scheduled_date).all()
    day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    return render_template('dashboard.html', subjects=subjects, upcoming_assessments=upcoming_assessments, todays_tasks=todays_tasks, day_names=day_names, today=today)

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
    return render_template('subject_detail.html', subject=subject, today=date.today())

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


with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, port=5000)