from flask import render_template, request, session, redirect, url_for
from mysql_db import connect_DB
from datetime import timedelta
from passlib.hash import sha256_crypt

def authenticate(app):
    
    error = ""

    # This bit is to erase the error login messages after a page reload and the message has been read
    if session.get('read_message') == 0:
        session['read_message'] = 1
    elif session.get('read_message') == 1:
        session['read_message'] = 2
        session['login_message'] = ""

    if request.method == 'POST':
        # Imports form data from login.html
        username = request.form.get('form_username') 
        password = request.form.get('form_password')
        attempt = {}
        
        if 'attempt' in session:
            attempt = session.get('attempt')
            if not username in attempt.keys():
                attempt[username] = 0
        else:
            attempt = {username: 0}
            
        # Blocks --one-- specific user from excessive login attempts
        # They can still try to login with a different username which is not locked
        if attempt.get(username) >= 3:
            session['login_message'] = "Too many failed attempts. Please wait 5 minutes."
            session['read_message'] = 0
            app.permanent_session_lifetime = timedelta(minutes=5)
            return redirect(url_for('login'))
        
        else:
            # Checks if fields are filled out
            if (username) and (password):
                try:
                    # Connecting to the database
                    mydb = connect_DB()
                    cursor = mydb.cursor()
                    # Search DB for username and return salt
                    cursor.execute("SELECT salt FROM account WHERE username = %s", (username,))
                    result_salt = cursor.fetchone()
                    # Checks if username does not exist
                    if result_salt is None:
                        print("post then wrong user")
                        session['login_message'] = "Incorrect username and/or password!"
                        session['read_message'] = 0
                        attempt_n = attempt.get(username)
                        attempt_n += 1
                        attempt[username] = attempt_n
                        session['attempt'] = attempt
                        return redirect(url_for('login'))
                    # If username exists
                    else:
                        cursor.execute("SELECT hash FROM account WHERE username = %s", (username,))
                        result_hash = cursor.fetchone()
                        hash = ''.join(result_hash)
                        salt = ''.join(result_salt)
                        salted_password = password + salt
                        password_compared = pass_compare(salted_password, hash)
                        if password_compared == True:
                            session['login_message'] = ""
                            # Creates session with username
                            # session.permanent = True
                            app.permanent_session_lifetime = timedelta(minutes=15)
                            session.permanent = True
                            session['user'] = username
                            session.pop('attempt', None)
                            cursor.execute("SELECT id FROM account WHERE username = %s", (username,))
                            result_id = cursor.fetchone()
                            id = ''.join(map(str, result_id))
                            session['id'] = id
                            return redirect(url_for('calendar'))           
                        # Incorrect credentials
                        else:
                            session['login_message'] = "Incorrect password!"
                            session['read_message'] = 0
                            attempt_n = attempt.get(username)
                            attempt_n += 1
                            attempt[username] = attempt_n
                            session['attempt'] = attempt
                            return redirect(url_for('login'))
                # Handles database connection errors
                except:
                    error = "Unknown Database Error"
                    return redirect(url_for('login'))
            else:
                error = "Fill in all fields"
                return redirect(url_for('login'))
    return render_template('login.html', message=session.get('login_message'), error=error)

def get_id():
    global id
    return id

def set_message():
    if session.get('read_message'):
        session['login_message'] = ""
    else:
        session['read_message'] = True

def pass_compare(salted_pass, hash_p):
    return sha256_crypt.verify(salted_pass, hash_p)
