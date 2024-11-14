from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Register')
    jlpt_level = SelectField('JLPT Level', choices=[('N1', 'N1'), ('N2', 'N2'), ('N3', 'N3'), ('N4', 'N4'), ('N5', 'N5')], coerce=int, default=5)
