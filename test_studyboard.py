# my automated tests for Studyboard, run from the project folder with:
#   python -m pytest test_studyboard.py -v
# it runs on an in memory database so it never touches my real studyboard.db,
# and the Groq call is swapped out with a fake so no test are ever outputted.

import os
import io
from datetime import date, timedelta
# this has to happen before app gets imported, so config picks up the in memory
# database instead of the real sqlite file
os.environ['DATABASE_URL'] = 'sqlite://'
import pytest
import app as app_module
from app import (app, calculate_weighted_grade, calculate_required_mark,
                 get_grade_summary, build_fallback_subtasks, safe_filename,
                 get_topic_stats)
from models import (db, User, Subject, Assessment, Task, TodoItem, SubjectFile,
                    Topic, Flashcard, FlashcardReview)
TODAY = date.today()
# This part is the setup, a new database for every test plus some shortcuts so the tests below stay short.


@pytest.fixture
def client():
    # empty database for every single test so they cannot leak into each other. CSRF is off here because these tests check what the routes do, the
    # token plumbing is a Flask-WTF feature.
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.app_context():
        db.drop_all()
        db.create_all()
    with app.test_client() as c:
        yield c


# kills the real Groq call so creating an assessment takes the fallback path
@pytest.fixture
def no_ai(monkeypatch):
    monkeypatch.setattr(app_module, 'generate_subtasks', lambda *a, **k: None)


def register(client, email, password='password123'):
    return client.post('/register', data={
        'email': email, 'password': password, 'confirm_password': password
    }, follow_redirects=True)


def login(client, email, password='password123'):
    return client.post('/login', data={'email': email, 'password': password},
                       follow_redirects=True)

# registers, logs in, and hands back the user id
def make_user(client, email='james@test.com'):
    register(client, email)
    login(client, email)
    with app.app_context():
        return User.query.filter_by(email=email).first().id


def make_subject(client, name='Biology'):
    client.post('/subject/new', data={
        'name': name, 'colour': '#4A90D9', 'year_level': 'Year 12'
    }, follow_redirects=True)
    with app.app_context():
        return Subject.query.filter_by(name=name).first().id


def make_assessment(client, subject_id, name='Trial Exam', days_out=14,
                    weighting='25', a_type='Essay', text='', file_tuple=None):
    data = {
        'name': name,
        'due_date': (TODAY + timedelta(days=days_out)).isoformat(),
        'weighting': weighting,
        'assessment_type': a_type,
        'task_notification': text,
    }
    if file_tuple:
        data['task_file'] = file_tuple
    resp = client.post(f'/subject/{subject_id}/assessment/new', data=data,
                       content_type='multipart/form-data', follow_redirects=True)
    with app.app_context():
        a = Assessment.query.filter_by(name=name).first()
        return (a.id if a else None), resp


def make_topic_with_card(client, subject_id, topic='Photosynthesis'):
    client.post('/flashcard/new', data={
        'subject_id': str(subject_id), 'topic_name': topic,
        'question': 'What are the reactants?', 'answer': 'CO2 and water'
    }, follow_redirects=True)
    with app.app_context():
        t = Topic.query.filter(db.func.lower(Topic.name) == topic.lower()).first()
        card = t.flashcards[0]
        return t.id, card.id

# This part is for registering and logging in.
def test_register_creates_user(client):
    # the basic happy path, sign up and the row exists with a hash not a password
    resp = register(client, 'new@test.com')
    assert b'Account created' in resp.data
    with app.app_context():
        u = User.query.filter_by(email='new@test.com').first()
        assert u is not None
        assert u.password_hash != 'password123'


def test_register_duplicate_email_rejected(client):
    # same email twice should be knocked back with the vague message on purpose
    register(client, 'dupe@test.com')
    resp = register(client, 'dupe@test.com')
    assert b'Unable to create account' in resp.data


def test_login_wrong_password_rejected(client):
    register(client, 'james@test.com')
    resp = client.post('/login', data={
        'email': 'james@test.com', 'password': 'wrongpassword'
    }, follow_redirects=True)
    assert b'Invalid email or password' in resp.data


def test_dashboard_requires_login(client):
    # not logged in means a change to the login page.
    resp = client.get('/dashboard')
    assert resp.status_code == 302
    assert '/login' in resp.headers['Location']


def test_security_headers_present(client):
    # the after_request hook should stamp these on every response
    resp = client.get('/login')
    assert resp.headers.get('X-Content-Type-Options') == 'nosniff'
    assert resp.headers.get('X-Frame-Options') == 'SAMEORIGIN'

# This part is for subjects, and for making sure you cannot get at anyone else's.
def test_create_subject(client):
    make_user(client)
    sid = make_subject(client)
    with app.app_context():
        assert Subject.query.get(sid).name == 'Biology'


def test_subject_ownership_blocked(client):
    # user two should never be able to open user one's subject
    make_user(client, 'one@test.com')
    sid = make_subject(client)
    client.get('/logout')
    make_user(client, 'two@test.com')
    resp = client.get(f'/subject/{sid}', follow_redirects=True)
    assert b'Access denied' in resp.data


def test_delete_subject_cascades(client, no_ai):
    # deleting a subject has to take its assessments, tasks and files with it.
    make_user(client)
    sid = make_subject(client)
    make_assessment(client, sid)
    client.post(f'/subject/{sid}/file/new', data={
        'subject_file': (io.BytesIO(b'my biology notes'), 'notes.txt')
    }, content_type='multipart/form-data', follow_redirects=True)
    client.post(f'/subject/{sid}/delete', follow_redirects=True)
    with app.app_context():
        assert Assessment.query.count() == 0
        assert Task.query.count() == 0
        assert SubjectFile.query.count() == 0

# This part is for uploading a task notification and everything that can go wrong.

def test_txt_upload_extracts_text_and_stores_file(client, no_ai):
    # the end to end path this whole project started on, upload a file and the
    # text lands in task_notification while the bytes land in the blob.
    make_user(client)
    sid = make_subject(client)
    content = b'Write a 1500 word essay on fiscal policy'
    aid, resp = make_assessment(client, sid,
                                file_tuple=(io.BytesIO(content), 'task.txt'))
    with app.app_context():
        a = Assessment.query.get(aid)
        assert a.task_notification == content.decode()
        assert a.task_file_name == 'task.txt'
        assert a.task_file_data == content


def test_wrong_extension_rejected(client, no_ai):
    # renaming an exe to sneak it past should hit the whitelist and bounce
    make_user(client)
    sid = make_subject(client)
    aid, resp = make_assessment(client, sid, name='Sneaky',
                                file_tuple=(io.BytesIO(b'MZ fake exe'), 'virus.exe'))
    assert aid is None
    assert b'Only PDF, Word' in resp.data


def test_oversize_file_rejected(client, no_ai, monkeypatch):
    # shrink the cap instead of building an actual 5MB file, same code path
    monkeypatch.setattr(app_module, 'MAX_FILE_SIZE', 10)
    make_user(client)
    sid = make_subject(client)
    aid, resp = make_assessment(client, sid, name='Huge',
                                file_tuple=(io.BytesIO(b'x' * 50), 'big.txt'))
    assert aid is None
    assert b'too large' in resp.data


def test_old_doc_gets_helpful_message(client, no_ai):
    # python-docx cannot read the old binary format so we tell them to convert
    make_user(client)
    sid = make_subject(client)
    aid, resp = make_assessment(client, sid, name='Legacy',
                                file_tuple=(io.BytesIO(b'old word'), 'task.doc'))
    assert aid is None
    assert b'save it as .docx' in resp.data

# fake the Groq response so the AI branch runs without touching the network
def test_ai_path_saves_subtasks_with_descriptions(client, monkeypatch):
    fake_plan = [
        {'title': 'Read the marking criteria', 'description': 'Go through the notification properly', 'days_before_due': 10},
        {'title': 'Write the draft', 'description': 'Get the 1500 words down', 'days_before_due': 4},
    ]
    monkeypatch.setattr(app_module, 'generate_subtasks', lambda *a, **k: fake_plan)
    make_user(client)
    sid = make_subject(client)
    aid, resp = make_assessment(client, sid, text='Essay on fiscal policy')
    assert b'AI study plan' in resp.data
    with app.app_context():
        tasks = Task.query.filter_by(assessment_id=aid).all()
        assert len(tasks) == 2
        assert tasks[0].description is not None

# AI dies, student still gets a plan, and the flash says which path ran
def test_fallback_path_when_ai_unavailable(client, no_ai):
    make_user(client)
    sid = make_subject(client)
    aid, resp = make_assessment(client, sid, text='Essay on fiscal policy')
    assert b'standard' in resp.data
    with app.app_context():
        tasks = Task.query.filter_by(assessment_id=aid).all()
        assert len(tasks) == 5
        assert all(t.description is None for t in tasks)


def test_fallback_never_schedules_before_today(client, no_ai):
    # due tomorrow means everything gets squeezed forward, nothing in the past
    make_user(client)
    sid = make_subject(client)
    aid, _ = make_assessment(client, sid, days_out=1, text='quick task')
    with app.app_context():
        for t in Task.query.filter_by(assessment_id=aid).all():
            assert t.scheduled_date >= TODAY


def test_edit_preserves_text_when_file_attached(client, no_ai):
    # editing just the name with the textarea blank must not
    # wipe the extracted text while a file is still attached
    make_user(client)
    sid = make_subject(client)
    content = b'Write a 1500 word essay on fiscal policy'
    aid, _ = make_assessment(client, sid, file_tuple=(io.BytesIO(content), 'task.txt'))
    client.post(f'/assessment/{aid}/edit', data={
        'name': 'Renamed Exam',
        'due_date': (TODAY + timedelta(days=14)).isoformat(),
        'weighting': '25', 'assessment_type': 'Essay', 'task_notification': ''
    }, content_type='multipart/form-data', follow_redirects=True)
    with app.app_context():
        a = Assessment.query.get(aid)
        assert a.name == 'Renamed Exam'
        assert a.task_notification == content.decode()
        assert a.task_file_name == 'task.txt'


def test_assessment_file_ownership(client, no_ai):
    # user two hitting the file url directly gets denied, not the PDF
    make_user(client, 'one@test.com')
    sid = make_subject(client)
    aid, _ = make_assessment(client, sid, file_tuple=(io.BytesIO(b'secret task'), 'task.txt'))
    client.get('/logout')
    make_user(client, 'two@test.com')
    resp = client.get(f'/assessment/{aid}/file', follow_redirects=True)
    assert b'Access denied' in resp.data
    assert b'secret task' not in resp.data


# This part is for to-dos and the Today list on the dashboard.
def test_todo_tomorrow_not_in_today(client):
    # a to-do dated tomorrow should stay off today's dashboard list
    make_user(client)
    sid = make_subject(client)
    client.post('/todo/new', data={
        'title': 'Future thing', 'subject_id': str(sid),
        'scheduled_date': (TODAY + timedelta(days=1)).isoformat()
    }, follow_redirects=True)
    resp = client.get('/dashboard')
    assert b'Future thing' not in resp.data


def test_completed_today_stays_visible(client):
    # ticking something off today keeps it on screen in its done state instead
    # of it vanishing the second you tick it
    make_user(client)
    sid = make_subject(client)
    client.post('/todo/new', data={
        'title': 'Chem prac writeup', 'subject_id': str(sid),
        'scheduled_date': TODAY.isoformat()
    }, follow_redirects=True)
    with app.app_context():
        tid = TodoItem.query.first().id
    client.post(f'/todo/{tid}/toggle', follow_redirects=True)
    resp = client.get('/dashboard')
    assert b'Chem prac writeup' in resp.data
    with app.app_context():
        assert TodoItem.query.get(tid).status == 'Complete'


def test_todo_ownership_checked_server_side(client):
    # the dropdown only shows your subjects but anyone can POST any id, so the
    # server has to check ownership itself
    make_user(client, 'one@test.com')
    sid = make_subject(client)
    client.get('/logout')
    make_user(client, 'two@test.com')
    make_subject(client, 'Chemistry')
    resp = client.post('/todo/new', data={
        'title': 'Evil todo', 'subject_id': str(sid),
        'scheduled_date': TODAY.isoformat()
    }, follow_redirects=True)
    with app.app_context():
        assert TodoItem.query.count() == 0


def test_referrer_open_redirect_blocked(client):
    # the referrer header is browser controlled, so a toggle should never bounce
    # someone off to an outside site even if the header says to
    make_user(client)
    sid = make_subject(client)
    client.post('/todo/new', data={
        'title': 'Toggle me', 'subject_id': str(sid),
        'scheduled_date': TODAY.isoformat()
    }, follow_redirects=True)
    with app.app_context():
        tid = TodoItem.query.first().id
    resp = client.post(f'/todo/{tid}/toggle',
                       headers={'Referer': 'https://evil.example.com/steal'})
    assert resp.status_code == 302
    assert 'evil.example.com' not in resp.headers['Location']
    assert '/dashboard' in resp.headers['Location']

# This part is for flashcards and working out which topics are weak.

def test_topic_names_merge_case_insensitively(client):
    make_user(client)
    sid = make_subject(client)
    make_topic_with_card(client, sid, 'Photosynthesis')
    client.post('/flashcard/new', data={
        'subject_id': str(sid), 'topic_name': '  photosynthesis ',
        'question': 'Where does it happen?', 'answer': 'Chloroplasts'
    }, follow_redirects=True)
    with app.app_context():
        assert Topic.query.count() == 1
        assert Flashcard.query.count() == 2


def test_one_lucky_guess_stays_weak(client):
    # one correct answer at 100 percent still sits in work on, because
    # MIN_REVIEWS_FOR_STRONG dosn't call a single guess mastery
    uid = make_user(client)
    sid = make_subject(client)
    tid, cid = make_topic_with_card(client, sid)
    client.post(f'/flashcard/{cid}/review', json={'was_correct': True})
    with app.app_context():
        strong, work_on = get_topic_stats(uid)
        assert len(strong) == 0
        assert work_on[0]['accuracy'] == 100


def test_three_correct_goes_strong(client):
    uid = make_user(client)
    sid = make_subject(client)
    tid, cid = make_topic_with_card(client, sid)
    for _ in range(3):
        client.post(f'/flashcard/{cid}/review', json={'was_correct': True})
    with app.app_context():
        strong, work_on = get_topic_stats(uid)
        assert len(strong) == 1
        assert strong[0]['accuracy'] == 100


def test_mostly_wrong_lands_in_work_on(client):
    uid = make_user(client)
    sid = make_subject(client)
    tid, cid = make_topic_with_card(client, sid)
    for correct in [True, False, False, False]:
        client.post(f'/flashcard/{cid}/review', json={'was_correct': correct})
    with app.app_context():
        strong, work_on = get_topic_stats(uid)
        assert len(strong) == 0
        assert work_on[0]['accuracy'] == 25


# user two poking someone else's card gets a JSON 403, no review row
def test_review_ownership_returns_403(client):
    make_user(client, 'one@test.com')
    sid = make_subject(client)
    tid, cid = make_topic_with_card(client, sid)
    client.get('/logout')
    make_user(client, 'two@test.com')
    resp = client.post(f'/flashcard/{cid}/review', json={'was_correct': True})
    assert resp.status_code == 403
    with app.app_context():
        assert FlashcardReview.query.count() == 0


def test_deleting_last_card_deletes_topic(client):
    make_user(client)
    sid = make_subject(client)
    tid, cid = make_topic_with_card(client, sid)
    client.post(f'/flashcard/{cid}/delete', follow_redirects=True)
    with app.app_context():
        assert Flashcard.query.count() == 0
        assert Topic.query.count() == 0


# This part is the predicted grade maths, checked against calculations.
def seed_completed(sid, mark, weighting):
    # drops a completed marked assessment into the db for the maths tests
    with app.app_context():
        a = Assessment(name='Seeded', due_date=TODAY + timedelta(days=30),
                       weighting=weighting, assessment_type='Essay',
                       status='Completed', mark=mark, subject_id=sid)
        db.session.add(a)
        db.session.commit()

# this part tests a bunch of perecent tasks to target 
def test_weighted_grade_no_marks_returns_zero(client):
    make_user(client)
    sid = make_subject(client)
    with app.app_context():
        assert calculate_weighted_grade(sid) == 0
        assert get_grade_summary(Subject.query.get(sid))['has_marks'] is False


def test_need_perfect_score_case(client):
    make_user(client)
    sid = make_subject(client)
    seed_completed(sid, 60, 50)
    with app.app_context():
        current = calculate_weighted_grade(sid)
        assert current == 60.0
        assert calculate_required_mark(sid, 80, current) == 100.0


def test_realistic_required_mark_case(client):
    make_user(client)
    sid = make_subject(client)
    seed_completed(sid, 70, 20)
    with app.app_context():
        current = calculate_weighted_grade(sid)
        assert calculate_required_mark(sid, 75, current) == 76.2


def test_impossible_target_flagged(client):
    make_user(client)
    sid = make_subject(client)
    seed_completed(sid, 40, 60)
    with app.app_context():
        summary = get_grade_summary(Subject.query.get(sid))
        assert summary['impossible'] is True


def test_already_achieved_flagged(client):
    make_user(client)
    sid = make_subject(client)
    seed_completed(sid, 95, 70)
    with app.app_context():
        with app.test_request_context():
            pass
        subject = None
    with app.app_context():
        subject = Subject.query.get(sid)
        subject.target_grade = 60
        db.session.commit()
        summary = get_grade_summary(Subject.query.get(sid))
        assert summary['achieved'] is True


def test_target_validated_server_side(client):
    make_user(client)
    sid = make_subject(client)
    resp = client.post(f'/subject/{sid}/target', data={'target_grade': '150'},
                       follow_redirects=True)
    assert b'between 1 and 100' in resp.data
    with app.app_context():
        assert Subject.query.get(sid).target_grade == 80

# This part is the tour and a couple of leftovers

def test_tour_shows_once_then_never_again(client):
    # brand new account gets the autostart flag, marking it seen kills it for good
    make_user(client)
    resp = client.get('/dashboard')
    assert b'data-sb-autostart' in resp.data
    client.post('/tour/seen')
    resp = client.get('/dashboard')
    assert b'data-sb-autostart' not in resp.data
    with app.app_context():
        assert User.query.first().has_seen_tour is True


def test_safe_filename_keeps_extension(client):
     # secure_filename strips non ascii which can destroy the whole name including
    # the dot, so I bolted the extension back on
    result = safe_filename('日本語ノート.pdf')
    assert result.endswith('.pdf')
    assert '.' in result