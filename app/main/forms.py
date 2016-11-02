from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, SelectField, BooleanField
from wtforms.validators import DataRequired, Length, Regexp, Email
from wtforms import ValidationError
from flask_pagedown.fields import PageDownField
from ..models import Role, User


class NameForm(FlaskForm):
    name = StringField('What is your name?', validators=[DataRequired()])
    submit = SubmitField('Submit')


class EditProfileForm(FlaskForm):
    realname = StringField('Realname', validators=[Length(0, 64)])
    location = StringField('Location', validators=[Length(0, 64)])
    self_info = TextAreaField('Self Introduction')
    submit = SubmitField('Submit')

    def validate_email(self, email):
        if User.query.filter_by(email=email.data).first() and self.email != email:
            raise ValidationError('Email already registered.')

    def validate_username(self, username):
        if User.query.filter_by(username=username.data).first() and self.username != username:
            raise ValidationError('Username already in use.')


class EditProfileAdminForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Length(1, 64), Email()])
    username = StringField('Username', validators=[DataRequired(), Length(1, 64),
                                                   Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                                                   'Username must have only letters, numbers, underscores and dots')])
    role = SelectField('Role', coerce=int)
    realname = StringField('Real name', validators=[Length(0, 64)])
    location = StringField('Location', validators=[Length(0, 64)])
    self_info = TextAreaField('Self introduction')
    submit = SubmitField('Submit')

    def __init__(self, user, *args, **kwargs):
        super(EditProfileAdminForm, self).__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name, ) for role in Role.query.order_by(Role.name).all()]
        self.user = user

    def validate_email(self, email):
        if User.query.filter_by(email=email.data).first() and self.email != email:
            raise ValidationError('Email already registered.')

    def validate_username(self, username):
        if User.query.filter_by(username=username.data).first() and self.username != username:
            raise ValidationError('Username already in use.')


class PostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(1, 64)])
    body = PageDownField('Write your articles here.', validators=[DataRequired()])
    visible = BooleanField('Let others see?')
    submit = SubmitField('Submit')


class SearchForm(FlaskForm):
    req = StringField('', validators=[DataRequired()])
    select1 = BooleanField('By username')
    select2 = BooleanField('By title')
    submit = SubmitField('Search')


class CheckinForm(FlaskForm):
    button = SubmitField('Check in')
