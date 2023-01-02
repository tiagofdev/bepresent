# Flask Web Framework
from flask import Flask

# Function Sources
import os
from authentication import *
from account_creation import *
from class_manager import *
from student_manager import *
from attendance_manager import *
from calendar_manager import show_calendar
from report_manager import *
from error import get_error
from datetime import timedelta

app = Flask(__name__)
app.config['SECRET_KEY'] = 'd#_jY2";º$4Êù~?}q¿ZÇ7¨'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=15)


# Refresh login activity timer
def refresh():
    app.permanent_session_lifetime = timedelta(minutes=15)
    session.permanent = True


# Home address reroute
@app.route('/')
def check_session():
    # main domain address redirects to calendar page if logged on
    if 'user' not in session:
        return redirect(url_for('login'))
    else:
        refresh()
        return redirect(url_for('calendar'))


# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    return authenticate(app)


# Signup Page
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    return create_account()


# Calendar
@app.route('/calendar', methods=['GET', 'POST'])
def calendar():
    if 'user' in session:
        refresh()
        return show_calendar(session.get('id'))
    else:
        return redirect(url_for('logout'))


# Show all students
@app.route('/students', methods=['GET', 'POST'])
def students():
    if 'user' in session:
        refresh()
        return show_students(session.get('id'))
    else:
        return redirect(url_for('logout'))


# Student info
@app.route('/studentinfo', methods=['GET', 'POST'])
def studentinfo():
    if 'user' in session:
        refresh()
        return get_student_info(session.get('id'))
    else:
        return redirect(url_for('logout'))


# Edit students
@app.route('/editstudent', methods=['GET', 'POST'])
def editstudent():
    if 'user' in session:
        refresh()
        return edit_student(session.get('id'))
    else:
        return redirect(url_for('logout'))


# Show all classes
@app.route('/classes', methods=['GET', 'POST'])
def classes():
    if 'user' in session:
        refresh()
        return show_classes(session.get('id'))
    else:
        return redirect(url_for('logout'))


# Class info
@app.route('/classinfo', methods=['GET', 'POST'])
def classinfo():
    if 'user' in session:
        refresh()
        return get_class_info()
    else:
        return redirect(url_for('logout'))


# Edit class
@app.route('/editclass', methods=['GET', 'POST'])
def editclass():
    if 'user' in session:
        refresh()
        return edit_class(session.get('id'))
    else:
        return redirect(url_for('logout'))


# Attendance
@app.route('/attendance', methods=['GET', 'POST'])
def attendance():
    if 'user' in session:
        refresh()
        return take_attendance()
    else:
        return redirect(url_for('logout'))


# Reports
@app.route('/reports', methods=['GET', 'POST'])
def reports():
    if 'user' in session:
        refresh()
        return get_reports()
    else:
        return redirect(url_for('logout'))


@app.route('/about', methods=['GET'])
def about():
    return render_template('about.html')


@app.route('/error', methods=['GET', 'POST'])
def error():
    return get_error(session.get(id))


@app.route('/logout')
def logout():
    # Kills the user session, logging them out
    session.pop('login_message', None)
    session.pop('attempt', None)
    session.pop('user', None)
    session.pop('id', None)
    session.pop('class_id', None)
    session.pop('class_dates', None)
    session.pop('prep_data', None)
    session.pop('student_info', None)
    session.pop('overlap', None)
    session.pop('class_exists', None)
    session.pop('student_exists', None)
    session.pop('atten_date', None)
    session.pop('today', None)
    session.pop('month', None)
    session.pop('year', None)
    session.clear()
    return redirect(url_for('login'))


app.run(debug=True, port=int(os.environ.get("PORT", 8080)), host='0.0.0.0', threaded=True)
