from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FloatField, \
    DateField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length, \
    NumberRange, ValidationError
from datetime import date


class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[
        DataRequired(message='All fields are required'),
        Email(message='Please enter a valid email address'),
        Length(max=150)
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message='All fields are required'),
        Length(min=8, message='Password must be at least 8 characters')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(message='All fields are required'),
        EqualTo('password', message='Passwords must match')
    ])
    submit = SubmitField('Create Account')


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[
        DataRequired(message='All fields are required'),
        Email(message='Please enter a valid email address')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message='All fields are required')
    ])
    submit = SubmitField('Log In')

class SubjectForm(FlaskForm):
    name = SelectField('Subject', validators=[DataRequired(message='Please select a subject')])
    colour = StringField('Colour', default='#4A90D9')
    year_level = SelectField('Year Level', choices=[
        ('Year 11', 'Year 11'),
        ('Year 12', 'Year 12')
    ], default='Year 12')
    submit = SubmitField('Save Subject')


class AssessmentForm(FlaskForm):
    name = StringField('Assessment Name', validators=[
        DataRequired(message='Assessment name is required'),
        Length(max=200)
    ])
    due_date = DateField('Due Date', validators=[
        DataRequired(message='Due date is required')
    ])
    weighting = FloatField('Weighting (%)', validators=[
        DataRequired(message='Weighting is required'),
        NumberRange(min=1, max=100, message='Weighting must be between 1 and 100')
    ])
    assessment_type = SelectField('Type', choices=[
        ('Assignment', 'Assignment'),
        ('Essay', 'Essay'),
        ('Exam', 'Exam'),
        ('Practical', 'Practical'),
        ('Presentation', 'Presentation'),
        ('Research Task', 'Research Task'),
        ('Other', 'Other')
    ])
    task_notification = TextAreaField('Task Notification (optional)',
                                     validators=[Length(max=20000)])
    submit = SubmitField('Save Assessment')

    def validate_due_date(self, field):
        if field.data and field.data < date.today():
            raise ValidationError('Due date must be a future date')


class MarkForm(FlaskForm):
    mark = FloatField('Mark (%)', validators=[
        DataRequired(),
        NumberRange(min=0, max=100, message='Mark must be between 0 and 100')
    ])
    submit = SubmitField('Save Mark')


class TaskForm(FlaskForm):
    title = StringField('Task Title', validators=[
        DataRequired(message='Task title is required'),
        Length(max=200)
    ])
    scheduled_date = DateField('Scheduled Date', validators=[
        DataRequired(message='Scheduled date is required')
    ])
    submit = SubmitField('Add Task')


class FlashcardForm(FlaskForm):
    subject_id = SelectField('Subject', coerce=int, validators=[
        DataRequired(message='Pick a subject')
    ])
    topic_name = StringField('Topic', validators=[
        DataRequired(message='Give your card a topic, for example Photosynthesis'),
        Length(max=100)
    ])
    question = TextAreaField('Question', validators=[
        DataRequired(message='The question cannot be blank'),
        Length(max=1000)
    ])
    answer = TextAreaField('Answer', validators=[
        DataRequired(message='The answer cannot be blank'),
        Length(max=1000)
    ])
    submit = SubmitField('Save flashcard')


class TodoItemForm(FlaskForm):
    title = StringField('To-do', validators=[
        DataRequired(message='Give your to-do a title'),
        Length(max=200)
    ])
    subject_id = SelectField('Subject', coerce=int, validators=[
        DataRequired(message='Pick a subject for your to-do')
    ])
    scheduled_date = DateField('Date', validators=[
        DataRequired(message='Pick a date for your to-do')
    ])
    submit = SubmitField('Add to-do')