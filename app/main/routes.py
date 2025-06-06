
from flask import render_template, redirect, url_for
from flask_login import login_required, current_user
from . import main #. es el directorio actual (main)

@main.route('/')
@main.route('/index')
# @login_required # Descomentar para proteger la página principal
def index():
    # if not current_user.is_authenticated:
    #     return redirect(url_for('auth.login'))
    return render_template('main/index.html', title='Inicio')
