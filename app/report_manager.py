from flask import Flask, render_template, request, redirect, url_for, flash, session
from mysql_db import connect_DB
from datetime import date, datetime, timedelta


def get_reports():
    class_id = session.get('class_id')
    try:
        mydb = connect_DB()
        cursor = mydb.cursor()
    except:
        flash("Error connecting to database")
        return redirect(url_for('error'))
    # query to collect class info
    try:
        # Total Number of Days
        cursor.execute("SELECT COUNT(*) FROM class_dates WHERE class_id = %s", (class_id,))
        days = cursor.fetchall()
        
        # Check if any attendace has been taken
        cursor.execute("SELECT COUNT(*) FROM class_dates WHERE class_id = %s AND taken = 1", (class_id,))
        taken = cursor.fetchall()
        
        # Get all students for that class
        cursor.execute("SELECT id FROM enrollment WHERE class_id = %s", (class_id,))
        students = cursor.fetchall()
        ids_list = []
        if students:
            for ss in students:
                ids_list.append(ss[0])
        ids = tuple(ids_list)
        details = []
        class_dates = []
        if  taken[0][0] != 0 and students:
        
            # Getting information from all students
            # Names
            # # Present, # Late, # Absent, # Excused
            # We're getting a list with each of these bits
            # We're adding all of them to a final list called data
            """
            # Names
            query = ""SELECT CONCAT_WS('. ',name_last,name_first) AS name FROM student WHERE
            id IN (SELECT student_id FROM enrollment WHERE id IN {} )"".format(ids)
            cursor.execute(query)
            names_result = cursor.fetchall()
            names = list(sum(names_result,() ))
            """
            # Names
            # For some reason, the above commented block is not returning the matching names
            # The following loop gets the names in the correct order
            
            query = """SELECT CONCAT_WS('. ',name_last,name_first) AS name FROM student WHERE
            id IN (SELECT student_id from enrollment WHERE id = %s)"""
            names = []
            for i in ids:
                cursor.execute(query,(i,))
                name_result = cursor.fetchone()
                names.append(name_result[0])
            
            # For each student, get a count of each attendance
            # Present
            query = """SELECT CAST(SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) AS UNSIGNED)
            FROM attendance WHERE enrollment_id IN {} GROUP BY enrollment_id""".format(ids)
            cursor.execute(query)
            present_result = cursor.fetchall()
            present = list(sum(present_result, () ))
            
            # Late
            query = """SELECT CAST(SUM(CASE WHEN status = 'Partial' THEN 1 ELSE 0 END) AS UNSIGNED) 
            FROM attendance WHERE enrollment_id IN {} GROUP BY enrollment_id""".format(ids)
            cursor.execute(query)
            late_result = cursor.fetchall()
            late = list(sum(late_result, () ))
            
            # Absent
            query = """SELECT CAST(SUM(CASE WHEN status = 'Absent' THEN 1 ELSE 0 END) AS UNSIGNED) 
            FROM attendance WHERE enrollment_id IN {} GROUP BY enrollment_id""".format(ids)
            cursor.execute(query)
            absent_result = cursor.fetchall()
            absent = list(sum(absent_result, () ))
            
            # Excused
            query = """SELECT CAST(SUM(CASE WHEN status = 'Excused' THEN 1 ELSE 0 END) AS UNSIGNED) 
            FROM attendance WHERE enrollment_id IN {} GROUP BY enrollment_id""".format(ids)
            cursor.execute(query)
            excused_result = cursor.fetchall()
            excused = list(sum(excused_result, () ))
            
            stats = []
            for i in range(len(students)):
                ss = []
                ss.append(names[i])
                ss.append(absent[i])
                ss.append(present[i])
                ss.append(late[i])
                ss.append(excused[i])
                ss.append( str(round((present[i] + late[i]) * 100 / days[0][0] )))
                stats.append(ss)
            
        else:
            stats = []
            students = session.get('included')
            for i in students:
                ss = []
                ss.append(i[1])
                ss.append(0)
                ss.append(0)
                ss.append(0)
                ss.append(0)
                ss.append(0)
                stats.append(ss)
        # Dates
        class_dates = session.get('class_dates')
        for ss in students:
            query = """SELECT status FROM attendance WHERE enrollment_id = %s AND date IN (SELECT 
            DATE_FORMAT(date,'%Y-%m-%d') FROM class_dates WHERE class_id = %s)"""
            cursor.execute(query,(ss[0],class_id))
            dates_result = cursor.fetchall()
            dates = list(sum(dates_result, () ))
            details.append(dates)
            
    except:
        flash("Error getting report")
        return redirect(url_for('error'))
    
    data = session.get('prep_data')
    return render_template('reports.html', data_s = data,stats = stats, days = days[0][0], taken = taken[0][0],
        details = details, class_dates = class_dates)

