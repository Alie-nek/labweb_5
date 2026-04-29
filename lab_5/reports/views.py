from flask import render_template, request, flash, redirect, url_for, make_response
from flask_login import current_user, login_required
from sqlalchemy import func, desc
import csv
from io import StringIO
from datetime import datetime
import codecs

from models import db, VisitLog, User
from decorators import check_rights
from . import reports_bp

PER_PAGE = 20

@reports_bp.before_request
@login_required
def before_request():
    """Защита всех маршрутов отчётов"""
    pass

@reports_bp.route('/logs')
def logs():
    page = request.args.get('page', 1, type=int)
    
    if current_user.has_role('Пользователь'):
        logs_query = VisitLog.query.filter_by(user_id=current_user.id)
    else:
        logs_query = VisitLog.query
    
    pagination = logs_query.order_by(desc(VisitLog.created_at)).paginate(
        page=page, per_page=PER_PAGE, error_out=False
    )
    logs = pagination.items
    
    return render_template('reports/logs.html', 
                         logs=logs, 
                         pagination=pagination,
                         has_admin_role=current_user.has_role('Администратор'))

@reports_bp.route('/pages-report')
@check_rights('view_logs_all')
def pages_report():
    stats = db.session.query(
        VisitLog.path,
        func.count(VisitLog.id).label('count')
    ).group_by(VisitLog.path).order_by(desc('count')).all()
    
    return render_template('reports/pages_report.html', stats=stats)

@reports_bp.route('/users-report')
@check_rights('view_logs_all')
def users_report():
    user_stats = db.session.query(
        VisitLog.user_id,
        func.count(VisitLog.id).label('count')
    ).filter(VisitLog.user_id.isnot(None)) \
     .group_by(VisitLog.user_id).order_by(desc('count')).all()
    
    anonymous_count = VisitLog.query.filter(VisitLog.user_id.is_(None)).count()
    
    users = {u.id: u for u in User.query.all()}
    
    return render_template('reports/users_report.html', 
                         user_stats=user_stats, 
                         anonymous_count=anonymous_count,
                         users=users)

@reports_bp.route('/export-pages-csv')
@check_rights('view_logs_all')
def export_pages_csv():
    stats = db.session.query(
        VisitLog.path,
        func.count(VisitLog.id).label('count')
    ).group_by(VisitLog.path).order_by(desc('count')).all()
    
    si = StringIO()
    
    si.write(codecs.BOM_UTF8.decode('utf-8'))
    
    cw = csv.writer(si, delimiter=';')
    cw.writerow(['№', 'Страница', 'Количество посещений'])
    
    for i, (path, count) in enumerate(stats, 1):
        cw.writerow([i, path, count])
    
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = f"attachment; filename=pages_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    output.headers["Content-type"] = "text/csv; charset=utf-8"
    
    return output

@reports_bp.route('/export-users-csv')
@check_rights('view_logs_all')
def export_users_csv():
    user_stats = db.session.query(
        VisitLog.user_id,
        func.count(VisitLog.id).label('count')
    ).filter(VisitLog.user_id.isnot(None)) \
     .group_by(VisitLog.user_id).order_by(desc('count')).all()
    
    anonymous_count = VisitLog.query.filter(VisitLog.user_id.is_(None)).count()
    
    users = {u.id: u for u in User.query.all()}
    
    si = StringIO()
    
    si.write(codecs.BOM_UTF8.decode('utf-8'))
    
    cw = csv.writer(si, delimiter=';')
    cw.writerow(['№', 'Пользователь', 'Количество посещений'])
    
    row_num = 1
    
    if anonymous_count > 0:
        cw.writerow([row_num, 'Неаутентифицированный пользователь', anonymous_count])
        row_num += 1
    
    for user_id, count in user_stats:
        if count > 0 and user_id in users:
            user = users[user_id]
            cw.writerow([row_num, user.full_name, count])
            row_num += 1
    
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = f"attachment; filename=users_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    output.headers["Content-type"] = "text/csv; charset=utf-8"
    
    return output