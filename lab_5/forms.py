from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, BooleanField
from wtforms.validators import DataRequired, Length, ValidationError, EqualTo
import re

class LoginForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember = BooleanField('Запомнить меня')

def validate_password_complexity(form, field):
    password = field.data
    
    if len(password) < 8:
        raise ValidationError('Пароль должен содержать не менее 8 символов')
    if len(password) > 128:
        raise ValidationError('Пароль должен содержать не более 128 символов')
    
    if not re.search(r'[A-ZА-Я]', password):
        raise ValidationError('Пароль должен содержать как минимум одну заглавную букву')
    if not re.search(r'[a-zа-я]', password):
        raise ValidationError('Пароль должен содержать как минимум одну строчную букву')
    
    if not re.search(r'\d', password):
        raise ValidationError('Пароль должен содержать как минимум одну цифру')
    
    if re.search(r'\s', password):
        raise ValidationError('Пароль не должен содержать пробелов')
    
    allowed_pattern = r'^[A-Za-zА-Яа-я0-9~!?@#$%^&*_\-+()\[\]{}><\/\\|"\'. ,:;]+$'
    if not re.match(allowed_pattern, password):
        raise ValidationError('Пароль содержит недопустимые символы')

def validate_username(form, field):
    username = field.data
    if len(username) < 5:
        raise ValidationError('Логин должен содержать не менее 5 символов')
    if not re.match(r'^[A-Za-z0-9]+$', username):
        raise ValidationError('Логин может содержать только латинские буквы и цифры')

class UserForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired(), validate_username])
    password = PasswordField('Пароль', validators=[DataRequired(), validate_password_complexity])
    last_name = StringField('Фамилия')
    first_name = StringField('Имя', validators=[DataRequired(message='Имя обязательно для заполнения')])
    patronymic = StringField('Отчество')
    role_id = SelectField('Роль', coerce=int, validators=[])

class UserEditForm(FlaskForm):
    last_name = StringField('Фамилия')
    first_name = StringField('Имя', validators=[DataRequired(message='Имя обязательно для заполнения')])
    patronymic = StringField('Отчество')
    role_id = SelectField('Роль', coerce=int, validators=[])

class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('Старый пароль', validators=[DataRequired()])
    new_password = PasswordField('Новый пароль', validators=[DataRequired(), validate_password_complexity])
    confirm_password = PasswordField('Повторите новый пароль', 
                                    validators=[DataRequired(), EqualTo('new_password', message='Пароли должны совпадать')])