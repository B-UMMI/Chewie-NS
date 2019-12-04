from flask import (current_app, render_template, flash, redirect, url_for, request, make_response, 
                Response, stream_with_context, send_from_directory)

from flask_security import (Security, SQLAlchemyUserDatastore, login_user, 
                           logout_user, current_user, user_registered)

from flask_login import login_required

#from app import (db, login_manager, datastore_cheat)

from . import front_end_blueprint


@front_end_blueprint.route('/')
@front_end_blueprint.route('/index')
@login_required
def index():
    return render_template('index.html', title='Home')


@front_end_blueprint.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))
    