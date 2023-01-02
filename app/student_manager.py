from flask import Flask, render_template, request, redirect, url_for, flash, session
from mysql_db import connect_DB


def edit_student(id):
    
    # Prepping student info from session
    student_id = session.get('student_id')
    student_info = session.get('student_info')
    p_name_first = ""
    p_name_last = ""
    if student_info:
        p_name_first = student_info[1]
        p_name_last = student_info[2]
    data = ()
    
    # POST
    if request.method == 'POST':
        
        # Collect HTML form data
        name_first = request.form.get('name_first')
        name_last = request.form.get('name_last')
        dob = request.form.get('dob')
        if dob == "":
            dob = None
        email = request.form.get('email')
        phone_number = request.form.get('phone_number')
        data = (name_first, name_last, dob, email, phone_number, id)
        
        # Persist data
        session['student_info'] = (None, name_first, name_last, dob, email, phone_number)
        
        # Connect to Database
        try:
            mydb = connect_DB()
            cursor = mydb.cursor()
        except:
            flash("failure to connect to DB")
            return redirect(url_for('error'))
        
        if 'save' in request.form:
            # Check if name already exists
            statement = "SELECT EXISTS (SELECT * FROM student WHERE name_first = %s AND name_last = %s"
            statement += " AND owner = %s)"
            cursor.execute(statement,(name_first,name_last,id))
            exists = cursor.fetchone()
            if student_id is None:
                if exists[0] == 0:
                    # Adding new student
                    try:
                        statement = "INSERT INTO student (name_first, name_last, dob, email, phone_number, owner)"
                        statement +=  "VALUES (%s,%s,%s,%s,%s,%s)"
                        cursor.execute(statement, (data))
                        mydb.commit()
                        return redirect(url_for('students'))
                    except:
                        flash("Unknown database Error!")
                        return redirect(url_for('error'))
                else:
                    # If student name already exists, reload and send a warning message
                    session['student_exists'] = "Name already in use"
                    return redirect(url_for('editstudent'))
            else:
                # Check if student name already exists
                cursor.execute("SELECT EXISTS(SELECT * FROM student WHERE name_first = %s AND name_last = %s AND owner = %s)",
                    (name_first,name_last,id))    
                exists = cursor.fetchone()
                # In update, if a new name is entered, it will updade if new name does not exist or 
                # if it is the same it was before
                if exists[0] == 0 or (exists[0] == 1 and name_first == p_name_first and name_last == p_name_last):
                    session['student_exists'] = None
                    try:
                        update_statement = "UPDATE student SET name_first = %s, name_last = %s, dob = %s,"
                        update_statement += "email = %s, phone_number = %s WHERE id = %s"
                        cursor.execute(update_statement,(name_first,name_last,dob,email,phone_number,student_id))
                        mydb.commit()
                        return redirect(url_for('students'))
                    except:
                        flash("error updating student info")
                        redirect(url_for('error'))
                else:
                    # If student name already exists, reload and send a warning message
                    session['name_exists'] = "Name already in use"
                    return redirect(url_for('editstudent'))
                
    return render_template('editstudent.html',si = student_info,message = session.get('name_exists'))


def show_students(id):
    session['student_info'] = None
    session['name_exists'] = None
    session['student_id'] = None
    if request.method == 'POST':
        if 'confirm' in request.form:
            delete_list = request.form.getlist('delete')
            if len(delete_list) > 1:
                delete_tuple = tuple(delete_list)
                statement_delete = "DELETE FROM student WHERE id IN {}".format(delete_tuple)
                try:
                    mydb = connect_DB()
                    cursor = mydb.cursor()
                    cursor.execute(statement_delete)
                    mydb.commit()
                    return redirect(url_for('students'))
                except:
                    flash("Error deleting student list")
                    return redirect(url_for('error'))
            elif len(delete_list) == 1:
                statement_delete = "DELETE FROM student WHERE id = %s"
                try:
                    mydb = connect_DB()
                    cursor = mydb.cursor()
                    cursor.execute(statement_delete,(delete_list[0],))
                    mydb.commit()
                    return redirect(url_for('students'))
                except:
                    flash("Error deleting student list")
                    return redirect(url_for('error'))
        else:
            session['student_id'] = request.form.get('studentid')
            return redirect(url_for('studentinfo'))
    try:
        mydb = connect_DB()
        cursor = mydb.cursor()
        query = "SELECT id, name_first, name_last,DATE_FORMAT(dob,'%m-%d-%y'),email, phone_number FROM student WHERE owner = %s ORDER BY name_last"
        cursor.execute(query, (id,))
        qres = cursor.fetchall()
        
    except:
        return redirect(url_for('error'))
    return render_template('students.html', data=qres)
    

def get_student_info(id):
    student_id = session.get('student_id')
    session['student_info'] = None
    session['class_id'] = None
    
    # Connecting to DB
    try:
        mydb = connect_DB()
        cursor = mydb.cursor()
    except:
        flash ("Error connecting to Database")
        return redirect(url_for('error'))
    
    try:
        # Get student info
        query = "SELECT id, name_first, name_last,DATE_FORMAT(dob,'%Y-%m-%d'),email, phone_number FROM student WHERE id = %s"
        cursor.execute(query, (student_id,))
        qres = cursor.fetchone()
        session['student_info'] = qres
        
        # Get student classes
        query = "SELECT id,name,sun,mon,tue,wed,thu,fri,sat,DATE_FORMAT(date_start,'%m-%d-%y'),"
        query += "DATE_FORMAT(date_end,'%m-%d-%y'),TIME_FORMAT(time_start,'%h:%i %p'),"
        query += "TIME_FORMAT(time_end, '%h:%i %p'),status FROM class WHERE id IN "
        query += "(SELECT class_id FROM enrollment WHERE student_id = %s) ORDER BY status"
        cursor.execute(query, (student_id,))
        classes = cursor.fetchall()
        
    except:
        return redirect(url_for('error'))
    
    if request.method == 'POST':
        if 'edit_button' in request.form:
            return redirect(url_for('editstudent'))
        if 'button_delete' in request.form:
            delete_student(student_id)
            return redirect(url_for('students'))
        session['class_id'] = request.form.get('classid')
        return redirect(url_for('classinfo'))
        
    return render_template('studentinfo.html', d = qres, classes = classes)

def delete_student(id):
    try:
        mydb = connect_DB()
        cursor = mydb.cursor()
        cursor.execute("DELETE FROM student WHERE id = %s",(id,))
        mydb.commit()
    except:
        flash("Error deleting student")