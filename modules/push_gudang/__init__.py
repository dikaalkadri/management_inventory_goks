from flask import Blueprint

push_gudang_bp = Blueprint('push_gudang', __name__, template_folder='../../templates')

from . import routes
