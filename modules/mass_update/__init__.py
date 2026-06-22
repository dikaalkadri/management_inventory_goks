from flask import Blueprint

mass_update_bp = Blueprint('mass_update', __name__, template_folder='../../templates')

from . import routes
