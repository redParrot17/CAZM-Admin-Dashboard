import flask
import flask_login
from pyfiles.gccutils.mygcc import MyGcc
import pyfiles.gccutils.asynccoursescraper as asynccs
from flask_login import login_required
from pyfiles.user import User
from pyfiles import database
from os import urandom

# setup flask application
app = flask.Flask(__name__)
app.secret_key = urandom(16)

# setup login manager
login_manager = flask_login.LoginManager()
login_manager.init_app(app)
users = {}

# setup database
database.initialize()


@login_manager.user_loader
def load_user(user_id):
    return users.get(user_id)

@login_manager.unauthorized_handler
def unauthorized():
    """This fires whenever the user tries accessing a secure page without being logged in."""
    return flask.redirect(flask.url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if flask.request.method == 'POST':
        username = flask.request.form['username']
        password = flask.request.form['password']

        if not username:
            error = 'Username is a required field.'
        elif not password:
            error = 'Password is a required field.'
        else:
            mygcc = MyGcc(username, password)
            if not mygcc.login():
                error = 'Password is incorrect.'
            else:
                user_id = mygcc.user_id
                user = User(user_id, username, password)
                users[user.get_id()] = user
                flask_login.login_user(user)
                mygcc.logout()

                return flask.redirect(flask.url_for('index'))
    return flask.render_template('login.html', error=error)

@app.route('/logout')
@login_required
def logout():
    # removes the user from cache
    user = flask_login.current_user
    if user.get_id() in users:
        del users[user.get_id()]

    # logs out the user
    flask_login.logout_user()

    return flask.redirect(flask.url_for('login'))

@app.route('/')
@login_required
def index():
    return flask.render_template('index.html')

@app.route('/courses', methods=['GET', 'POST'])
@login_required
def courses():
    if flask.request.method == 'POST':
        json = flask.request.get_json()
        if json is not None:

            to_create = json.get('create')
            to_change = json.get('change')
            to_delete = json.get('delete')
            to_resync = json.get('sync')

            if to_create is not None:
                database.create_entry(
                    to_create.get('code'),
                    to_create.get('name'),
                    to_create.get('term'),
                    to_create.get('credits', 0.0),
                    to_create.get('requisites', []))
            
            if to_change is not None:
                database.update_entry(
                    to_change.get('code'),
                    to_change.get('name'),
                    to_change.get('term'),
                    to_change.get('credits', 0.0),
                    to_change.get('requisites', []))

            if to_delete is not None:
                database.delete_entries(to_delete)

            if to_resync is not None:
                if to_resync:
                    user = flask_login.current_user
                    asynccs.start(user.username, user.password)
                else:
                    asynccs.stop()

            return flask.jsonify(success=True)
        return flask.jsonify(success=False)
    else:
        return flask.render_template('courses.html', syncing=asynccs.is_running)

@app.route('/students')
@login_required
def students():
    return flask.render_template('students.html')
