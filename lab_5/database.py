from models import db, Role, User

def init_db(app):
    with app.app_context():
        db.create_all()
        
        if not Role.query.first():
            roles = [
                Role(name='Администратор', description='Полный доступ к системе'),
                Role(name='Пользователь', description='Ограниченный доступ')
            ]
            for role in roles:
                db.session.add(role)
            db.session.commit()
            print("Роли созданы: Администратор, Пользователь")
        
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                first_name='Администратор',
                last_name='Системы',
                role_id=1  
            )
            admin.password = 'Admin123!'  
            db.session.add(admin)
            print("Создан администратор: admin / Admin123!")
        
        if not User.query.filter_by(username='user').first():
            user = User(
                username='user',
                first_name='Обычный',
                last_name='Пользователь',
                role_id=2  
            )
            user.password = 'User123!'  
            db.session.add(user)
            print("Создан пользователь: user / User123!")
        
        db.session.commit()