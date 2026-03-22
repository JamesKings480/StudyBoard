from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length


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