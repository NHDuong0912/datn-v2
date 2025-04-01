from flask import Blueprint, render_template
from flask_login import login_required
from flask_jwt_extended import get_jwt_identity
from app.models import User, Node
from app import db

dashboard = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@dashboard.route('/')
@login_required
def index():
    return render_template('dashboard/index.html')

@dashboard.route('/nodes')
@login_required
def nodes():
    return render_template('dashboard/nodes.html')

@dashboard.route('/nodes/<int:node_id>')
@login_required
def node_details(node_id):
    return render_template('dashboard/node_details.html', node_id=node_id)