import flask
import flask_login
from pyfiles.gccutils.mygcc import MyGcc
from pyfiles.gccutils.coursesearch import AsyncCourseScraper
from flask_login import login_required
from pyfiles.user import User
from pyfiles.database import Database
from os import urandom
import re

# declare shared variables
course_fetcher = None
# cached_courses = []
users = {}

# setup flask application
app = flask.Flask(__name__)
app.secret_key = urandom(16)

# setup login manager
login_manager = flask_login.LoginManager()
login_manager.init_app(app)


def validate_dict_integrity(course):
    code = course.get('code')
    name = course.get('name')
    hours = course.get('credits', 0.0)
    term = course.get('term')
    old_term = course.get('oldterm')
    requisites = course.get('requisites', [])

    # validate course code
    if code is None or \
            not isinstance(code, str) or \
            not re.match(r'[A-Z]{2,5}\s[0-9]{2,4}[A-Z ]*', code):
        return None, 'course code is invalid'

    # validate course name
    if not name or not isinstance(name, str):
        return None, 'course name is invalid'

    # validate course hours
    if isinstance(hours, str):
        try: hours = float(hours)
        except ValueError: pass
    if not isinstance(hours, float) and not isinstance(hours, int):
        return None, 'course credits is invalid'

    # validate course term
    if not isinstance(term, str) or \
            not re.match(r'[A-Za-z ]+\s[0-9]{4}', term):
        return None, 'course term is invalid'

    # validate course term
    if isinstance(old_term, str) and \
            not re.match(r'[A-Za-z ]+\s[0-9]{4}', old_term):
        return None, 'course old term is invalid'

    # validate requisites
    if not isinstance(requisites, list):
        return None, 'course requisites is invalid'

    semester, year = term.rsplit(' ', 1)
    year = int(year)

    result = {
        'code': code,
        'name': name,
        'credits': hours,
        'semester': semester,
        'year': year,
        'requisites': requisites
    }

    if old_term is not None:
        semester, year = old_term.rsplit(' ', 1)
        year = int(year)
        result['old_semester'] = semester
        result['old_year'] = year

    return result, None
    

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
    global course_fetcher
    database = Database('mysql.cnf')

    if flask.request.method == 'POST':
        json = flask.request.get_json()
        if json is not None:

            to_create = json.get('create')
            to_change = json.get('change')
            to_delete = json.get('delete')
            to_resync = json.get('sync')

            if to_create is not None:
                course, error = validate_dict_integrity(to_create)
                if not course:
                    print(error)
                else:
                    database.update_course(
                        code=course['code'],
                        name=course['name'],
                        hours=course['credits'],
                        semester=course['semester'],
                        year=course['year'],
                        requisites=course['requisites'])
            
            if to_change is not None and 'oldterm' in to_change:
                course, error = validate_dict_integrity(to_change)
                if not course:
                    print(error)
                else:
                    database.update_course(
                        code=course['code'],
                        old_semester=course['old_semester'],
                        old_year=course['old_year'],
                        name=course['name'],
                        hours=course['credits'],
                        semester=course['semester'],
                        year=course['year'],
                        requisites=course['requisites'])

            if to_delete is not None:
                delete_argument = []
                for code, term in to_delete:
                    semester, year = term.rsplit(' ', 1)
                    year = int(year)
                    delete_argument.append((code, semester, year))
                database.delete_courses(delete_argument)

            if to_resync is not None:
                if to_resync:
                    if not course_fetcher or not course_fetcher.is_running():
                        user = flask_login.current_user
                        course_fetcher = AsyncCourseScraper(user.username, user.password, 'mysql.cnf')
                        course_fetcher.start()
                elif course_fetcher:
                    course_fetcher.stop()
                    course_fetcher = None

            return flask.jsonify(success=True)
        return flask.jsonify(success=False)
    else:

        # check if webscraping is currently happening
        is_running = course_fetcher is not None and course_fetcher.is_running()

        # fetch the courses to display on the webpage
        all_courses = list(database.get_all_courses())  # if not is_running else cached_courses

        # respond with the requested webpage
        return flask.render_template('courses.html', syncing=is_running, data=all_courses)

@app.route('/students')
@login_required
def students():
    return flask.render_template('students.html')
