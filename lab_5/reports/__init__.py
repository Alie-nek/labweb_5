from flask import Blueprint

reports_bp = Blueprint('reports', __name__, 
                      template_folder='../templates/reports',
                      static_folder='../static')

from . import views