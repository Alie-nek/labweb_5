from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class Role(db.Model):
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200))
    
    users = db.relationship('User', backref='role', lazy=True)
    
    def __repr__(self):
        return f'<Role {self.name}>'

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    last_name = db.Column(db.String(50))
    first_name = db.Column(db.String(50), nullable=False)
    patronymic = db.Column(db.String(50))
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    visit_logs = db.relationship('VisitLog', backref='user', lazy=True)
    
    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')
    
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @property
    def full_name(self):
        parts = [self.last_name or '', self.first_name or '', self.patronymic or '']
        return ' '.join(filter(None, parts)).strip() or self.username
    
    @property
    def role_name(self):
        return self.role.name if self.role else 'Нет роли'
    
    def has_role(self, role_name):
        return self.role and self.role.name == role_name
    
    def __repr__(self):
        return f'<User {self.username}>'

class VisitLog(db.Model):
    __tablename__ = 'visit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def user_display(self):
        if self.user:
            return self.user.full_name
        return "Неаутентифицированный пользователь"
    
    def __repr__(self):
        return f'<VisitLog {self.path} {self.created_at}>'