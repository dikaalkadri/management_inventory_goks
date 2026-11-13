from flask import Blueprint

reset_so_bp = Blueprint('reset_so', __name__)

from . import routes
