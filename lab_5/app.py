from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Role, VisitLog
from forms import LoginForm, UserForm, UserEditForm, ChangePasswordForm
from database import init_db
from decorators import check_rights
from reports import reports_bp
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Пожалуйста, войдите для доступа к этой странице.'

app.register_blueprint(reports_bp, url_prefix='/reports')

@app.before_request
def log_visit():
    if request.path.startswith('/static') or request.path == '/favicon.ico':
        return
    
    if request.path.startswith('/reports/logs'):
        return
    
    log = VisitLog(
        path=request.path,
        user_id=current_user.id if current_user.is_authenticated else None
    )
    db.session.add(log)
    db.session.commit()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.context_processor
def inject_user_role():
    return dict(has_admin_role=current_user.has_role('Администратор') if current_user.is_authenticated else False)

@app.route('/')
def index():
    users = User.query.all()
    return render_template('index.html', users=users)

@app.route('/user/<int:user_id>')
@check_rights('view')
def view_user(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('user_view.html', user=user)

@app.route('/user/create', methods=['GET', 'POST'])
@login_required
@check_rights('create')
def create_user():
    form = UserForm()
    form.role_id.choices = [(r.id, r.name) for r in Role.query.all()]
    form.role_id.choices.insert(0, (0, 'Без роли'))
    
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash('Пользователь с таким логином уже существует', 'danger')
            return render_template('user_form.html', form=form, title='Создание пользователя')
        
        user = User(
            username=form.username.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data if form.last_name.data else None,
            patronymic=form.patronymic.data if form.patronymic.data else None,
            role_id=form.role_id.data if form.role_id.data != 0 else None
        )
        user.password = form.password.data
        
        try:
            db.session.add(user)
            db.session.commit()
            flash('Пользователь успешно создан', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при создании пользователя: {str(e)}', 'danger')
    
    return render_template('user_form.html', form=form, title='Создание пользователя')

@app.route('/user/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@check_rights('edit')
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    
    form = UserEditForm(obj=user)
    form.role_id.choices = [(r.id, r.name) for r in Role.query.all()]
    form.role_id.choices.insert(0, (0, 'Без роли'))
    
    if user.role_id is None:
        form.role_id.data = 0
    
    if current_user.has_role('Пользователь'):
        form.role_id.render_kw = {'disabled': True}
    
    if form.validate_on_submit():
        user.first_name = form.first_name.data
        user.last_name = form.last_name.data if form.last_name.data else None
        user.patronymic = form.patronymic.data if form.patronymic.data else None
        
        if current_user.has_role('Администратор'):
            user.role_id = form.role_id.data if form.role_id.data != 0 else None
        
        try:
            db.session.commit()
            flash('Пользователь успешно обновлен', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при обновлении пользователя: {str(e)}', 'danger')
    
    return render_template('user_form.html', form=form, user=user, title='Редактирование пользователя')

@app.route('/user/<int:user_id>/delete', methods=['POST'])
@login_required
@check_rights('delete')
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('Вы не можете удалить свою собственную учетную запись', 'danger')
        return redirect(url_for('index'))
    
    try:
        db.session.delete(user)
        db.session.commit()
        flash(f'Пользователь {user.full_name} успешно удален', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении пользователя: {str(e)}', 'danger')
    
    return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if not user and User.query.count() == 0 and form.username.data == 'admin' and form.password.data == 'Admin123!':
            role = Role.query.filter_by(name='Администратор').first()
            
            user = User(
                username='admin',
                first_name='Системный',
                last_name='Администратор',
                role_id=role.id if role else None
            )
            user.password = 'Admin123!'
            db.session.add(user)
            db.session.commit()
            flash('Создан администратор. Добро пожаловать!', 'info')
            login_user(user, remember=form.remember.data)
            return redirect(url_for('index'))
        
        if user and user.verify_password(form.password.data):
            login_user(user, remember=form.remember.data)
            flash(f'Добро пожаловать, {user.full_name}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Неверное имя пользователя или пароль', 'danger')
    
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('index'))

@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        if current_user.verify_password(form.old_password.data):
            current_user.password = form.new_password.data
            try:
                db.session.commit()
                flash('Пароль успешно изменен', 'success')
                return redirect(url_for('index'))
            except Exception as e:
                db.session.rollback()
                flash(f'Ошибка при смене пароля: {str(e)}', 'danger')
        else:
            flash('Неверный старый пароль', 'danger')
    
    return render_template('change_password.html', form=form)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        init_db(app)
    app.run(debug=True)