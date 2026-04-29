from functools import wraps
from flask import flash, redirect, url_for, request
from flask_login import current_user

def check_rights(action):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Необходимо авторизоваться для доступа к этой странице', 'warning')
                return redirect(url_for('login', next=request.url))
            
            user_id = kwargs.get('user_id')
            
            if current_user.has_role('Администратор'):
                return f(*args, **kwargs)
            
            if current_user.has_role('Пользователь'):
                if action == 'view' and user_id and int(user_id) != current_user.id:
                    flash('У вас недостаточно прав для просмотра профиля другого пользователя', 'danger')
                    return redirect(url_for('index'))
                
                if action == 'edit' and user_id and int(user_id) != current_user.id:
                    flash('У вас недостаточно прав для редактирования этого пользователя', 'danger')
                    return redirect(url_for('index'))
                
                if action == 'delete':
                    flash('У вас недостаточно прав для удаления пользователей', 'danger')
                    return redirect(url_for('index'))
                
                if action == 'create':
                    flash('У вас недостаточно прав для создания пользователей', 'danger')
                    return redirect(url_for('index'))
                
                if action == 'view_logs_all':
                    flash('У вас недостаточно прав для просмотра всех логов', 'danger')
                    return redirect(url_for('reports.logs'))
            
            if not current_user.role:
                flash('У вас недостаточно прав для доступа к данной странице', 'danger')
                return redirect(url_for('index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator