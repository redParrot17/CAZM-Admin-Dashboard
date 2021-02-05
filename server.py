import flask
import flask_login
from flask_login import login_required
from pyfiles.user import User
from os import urandom

app = flask.Flask(__name__)
app.secret_key = urandom(16)


#TODO: replace as soon as authentication backend is implemented
creds = {
    'demo-username': 'demo-pa$$word'
}
users = {}


# setup login manager
login_manager = flask_login.LoginManager()
login_manager.init_app(app)


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
        #elif creds.get(username, '') != password:
        #    error = 'Password is incorrect.'
        else:
            user_id = 1234
            user = User(user_id, username, password)
            users[user.get_id()] = user
            flask_login.login_user(user)

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

@app.route('/courses')
@login_required
def courses():
    return flask.render_template('courses.html')

@app.route('/students')
@login_required
def students():
    return flask.render_template('students.html')
    

@app.route('/test')
@login_required
def test():
    from pyfiles.gccutils.mygcc import MyGcc
    user = flask_login.current_user
    mygcc = MyGcc(user.username, user.password)

    with open('courses.json', 'w+') as f:
        f.write('[')

    last = None

    for course in mygcc.iter_all_courses():
        course.name = course.name.split('(')[0].strip()

        if last is None:
            last = course
        elif not last.is_same(course):
            with open('courses.json', 'a') as f:
                f.write(str(last.__dict__()) + ',')
            print(last.__dict__())
            last = course

    with open('courses.json', 'a') as f:
        f.write(str(last.__dict__()) + ']')
    print(last.__dict__())

    return 'Done'
