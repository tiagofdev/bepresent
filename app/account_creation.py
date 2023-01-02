from flask import Flask, render_template, request, redirect, url_for, flash
from mysql_db import connect_DB
from passlib.hash import sha256_crypt
import bcrypt

error = ''
message = ''

def create_account():
    global error
    global message
    if request.method == 'POST':
        if 'save' in request.form:
            username = request.form.get('form_username') 
            password = request.form.get('form_password')
            email = request.form.get('form_email')
            # Checks if form fields were not left empty
            if username and password and email:
                mydb = connect_DB()
                cursor = mydb.cursor()
                try:

                    # Checks if email already exists
                    cursor.execute("SELECT email FROM account WHERE email = %s", (email,))
                    result_email = cursor.fetchone()
                    if result_email is None:
                        # Checks if username already exists
                        cursor.execute("SELECT username FROM account WHERE username = %s", (username,))
                        result_username = cursor.fetchone()
                        # All checks cleared
                        if result_username is None:
                            bytestring = bcrypt.gensalt()
                            salt = str(bytestring, 'utf-8')
                            salted_pass = password + salt
                            hash = sha256_crypt.encrypt(salted_pass)
                            query = "INSERT INTO account (email, username, salt, hash) VALUES (%s, %s, %s, %s)"
                            cursor.execute(query, (email, username, salt, hash,))
                            mydb.commit()
                            message = "Account created"
                            error = ""
                            return redirect(url_for('signup'))
                        # Username already exists
                        else:
                            error = "Username unavailable! Choose a different username."
                            return redirect(url_for('signup'))
                    # Email already registered
                    else:
                        error = "An account associated with this email already exists!"
                        return redirect(url_for('signup'))
                #Handles database connection errors
                except:
                    error = "Unknown Database Error!"
                    cursor.execute("SHOW ERRORS")
                    res = cursor.fetchone()
                    if res is None:
                        error = "Sever down!"
                    else:
                        for r in res:
                            error.join(r, ",")
                    return redirect(url_for('signup'))
            # form fields not filled
            else:
                error = "Fill in all required fields!"
                return redirect(url_for('signup'))
    return render_template('signup.html', message=message, error=error)

