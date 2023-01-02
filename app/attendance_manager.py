from flask import Flask, render_template, request, redirect, url_for, flash, session
from mysql_db import connect_DB


# !!!!!!In order to delete a class, first I gotta remove all entries of that class id from enrollment in the name_enrollmentbase!!!!!!!
def take_attendance() :
    
    atten_date = session.get('atten_date')
    class_id = session.get('class_id')
    mydb = None
    cursor = None
    name_enrollment = []
    attendance_db = []
    # Connect to DB
    try:
        mydb = connect_DB()
        cursor = mydb.cursor()
    except:
        flash("Error connecting to database")
        return redirect(url_for('error'))
    
    # Get all students enrolled in that class
    try:
        get_ss_query = """SELECT CONCAT_WS(', ',name_last,name_first) AS name FROM student WHERE id IN (
            SELECT student_id FROM enrollment WHERE class_id = %s)"""
        cursor.execute(get_ss_query,(class_id,))
        qres = cursor.fetchall()
        cursor.execute("SELECT id FROM enrollment WHERE class_id = %s", (class_id,))
        qres2 = cursor.fetchall()
        # The two queries align names with their enrollment ids because they are both pulled by the same criteria ????
        # Merge the two queries into one array
        for e in range(len(qres)):
            # qres[e] only has 1 element, for some reason, qres[e][0] does not work!
            for x in qres[e]:
                name = x
            for x in qres2[e]:
                id = x
            name_enrollment.append((name,id))
        # Sort the resulting array by last name ascending after matching with enrollment ids
        name_enrollment.sort()
        # get class name
        cursor.execute("SELECT name FROM class WHERE id = %s", (class_id,))
        qres3 = cursor.fetchone()
        
    except:
        flash("Error getting enrollment students!")
        return redirect(url_for('error'))

    # check if attendance has been taken
    taken = 0
    try:
        cursor.execute("SELECT taken FROM class_dates WHERE class_id = %s AND date = %s",(class_id,atten_date))
        qres = cursor.fetchone()
        taken = qres[0]
    except:
        flash("error getting date status")
        return redirect(url_for('error'))

    # if taken collect each student attendance status for that date
    if taken:
        try:
            for n in name_enrollment:
                cursor.execute("SELECT status FROM attendance WHERE (enrollment_id = %s AND date = %s)",(n[1],atten_date))
                x = cursor.fetchone()
                # If class already taken and student was included in that attendance list
                if x:
                    attendance_db.append(x[0])
                # Case when class already taken but student was not included then, but added later 
                else:
                    attendance_db.append("Absent")
        except:
            flash("error collecting attendances")
            return redirect(url_for('error'))
    
    # Otherwise, just send a null??? array
    # Submitting HTML form
    if request.method == 'POST':
        
        if 'button_save' in request.form:
            
            # Collect attendace from client
            attendance_C = []
            for i in name_enrollment:
                attendance_C.append( (i[1], atten_date, request.form.get(str( i[1] )) ) )
                
            # If attendance has NOT already been taken
            if attendance_C:
                if (taken == 0):
                    try:
                        cursor.executemany("INSERT INTO attendance VALUES (%s,%s,%s)",(attendance_C))
                        # Set date as taken
                        cursor.execute("UPDATE class_dates SET taken = 1 WHERE (class_id = %s AND date = %s)",(class_id,atten_date))
                    except:
                        flash("Error saving attendance")
                        return redirect('error')
                
                # Otherwise update taken status only
                else:
                    try:
                        for x in attendance_C:
                            cursor.execute("UPDATE attendance SET status = %s WHERE (enrollment_id = %s AND date = %s)",(x[2],x[0],x[1]))
                    except:
                        flash("error updating attendance")
                        return redirect('error')
                mydb.commit()
            return redirect(url_for('classinfo'))
    return render_template("attendance.html",  atten_date_s = atten_date, name_enrollment_s = name_enrollment, attendance_s = attendance_db, name = qres3[0])