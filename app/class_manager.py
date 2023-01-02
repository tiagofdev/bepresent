from flask import render_template, request, Response, redirect, url_for, flash, session
from mysql_db import connect_DB
from datetime import datetime, timedelta

h = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11"]
m = ["00", "10", "15", "20", "30", "40", "45", "55"]


# !!!!!!In order to delete a class, first I gotta remove all entries of that class id from enrollment in the database!!!!!!!

def show_classes(id):
    session['class_id'] = None
    session['prep_data'] = None
    session['overlap'] = None
    session['class_exists'] = None
    session['included'] = None
    session['class_dates'] = None

    if request.method == 'POST':
        if 'newclass' in request.form:
            return redirect(url_for('editclass'))
        session['class_id'] = request.form.get('classid')
        return redirect(url_for('classinfo'))
    try:
        mydb = connect_DB()
        cursor = mydb.cursor()
        query = "SELECT id,name,sun,mon,tue,wed,thu,fri,sat,DATE_FORMAT(date_start,'%m-%d-%y'),DATE_FORMAT(date_end,'%m-%d-%y'),"
        query += "TIME_FORMAT(time_start,'%h:%i %p'),TIME_FORMAT(time_end, '%h:%i %p'),status FROM class WHERE owner = %s ORDER BY status"
        cursor.execute(query, (id,))
        qres = cursor.fetchall()
    except:
        return redirect(url_for('error'))
    #print("qres: ", qres)
    return render_template('classes.html', data=qres)


def get_class_info():
    class_id = session.get('class_id')
    session['prep_data'] = None
    session['atten_date'] = None
    session['included'] = None
    session['class_dates'] = None
    # Connecting to DB
    try:
        mydb = connect_DB()
        cursor = mydb.cursor()
    except:
        flash("Error connecting to database")
        return redirect(url_for('error'))
    # query to collect class info
    try:
        # General Info
        query = "SELECT id,name,sun,mon,tue,wed,thu,fri,sat,DATE_FORMAT(date_start,'%Y-%m-%d'),DATE_FORMAT(date_end,'%Y-%m-%d'),"
        query += "TIME_FORMAT(time_start,'%h:%i %p'),TIME_FORMAT(time_end, '%h:%i %p'),status FROM class WHERE id = %s"
        cursor.execute(query, (class_id,))
        prep_data = cursor.fetchone()
        session['prep_data'] = prep_data
        # Students enrolled
        included = []
        included = get_included(class_id)
        session['included'] = included
        # Progress
        cursor.execute("SELECT COUNT(*) FROM class_dates WHERE class_id = %s", (class_id,))
        dates = cursor.fetchall()
        cursor.execute("SELECT COUNT(*) FROM class_dates WHERE class_id = %s AND taken = 1", (class_id,))
        taken = cursor.fetchall()
        progress = 0
        if not dates[0][0] == 0:
            progress = str(round(taken[0][0] * 100 / dates[0][0]))
        # Most updated Attendance Rate
        # # of "Present" or "Late" attendance / ( # students x # taken attendance )
        query = "SELECT COUNT(*) FROM attendance WHERE (status = 'Present' OR status = 'Partial') AND enrollment_id IN ( SELECT id FROM enrollment WHERE class_id = %s)"
        cursor.execute(query, (class_id,))
        present = cursor.fetchone()
        rate = 0

        if len(included) != 0 and taken[0][0] != 0:
            rate = round((present[0] * 100) / (len(included) * taken[0][0]))

    except:
        flash("Error getting class data")
        return redirect(url_for('error'))

    # Query to collect class dates
    try:
        cursor.execute("SELECT DATE_FORMAT(date,'%Y-%m-%d'),taken FROM class_dates WHERE class_id = %s", (class_id,))
        qres = cursor.fetchall()
        session['class_dates'] = qres
    except:
        flash("Error getting class dates")
        return redirect(url_for('error'))

    # Client POST
    if request.method == "POST":
        if 'edit_button' in request.form:
            return redirect(url_for('editclass'))
        if 'attendance_button' in request.form:
            session['atten_date'] = request.form.get('date')
            return redirect(url_for('attendance'))
        if 'button_delete' in request.form:
            delete_class(class_id)
            return redirect(url_for('classes'))
        if 'button_reports' in request.form:
            return redirect(url_for('reports'))

    return render_template('classinfo.html', data_s=prep_data, dates=qres, progress_s=progress,
                           enrolled_students=included, rate=rate)


def get_included(class_id):
    try:
        mydb = connect_DB()
        cursor = mydb.cursor()
        # query to select students already enrolled in that class
        query = "SELECT id, CONCAT_WS(', ',name_last,name_first) AS name FROM student WHERE id IN (SELECT student_id FROM enrollment WHERE class_id = %s) ORDER BY name_last ASC"
        cursor.execute(query, (class_id,))
        included = cursor.fetchall()
        return included
    except:
        flash("Error getting enrolled")
        return redirect(url_for('error'))


def get_all(id):
    try:
        mydb = connect_DB()
        cursor = mydb.cursor()
        # query to select all students of account
        query = "SELECT id, CONCAT_WS(', ',name_last,name_first) AS name FROM student WHERE owner = %s ORDER BY name_last ASC"
        cursor.execute(query, (id,))
        students = cursor.fetchall()
        return students
    except:
        flash("error getting all students from DB")
        return redirect(url_for('error'))


def edit_class(id):
    available = ()
    included = ()
    prep_data = session.get('prep_data')
    if session.get('class_id') is not None:
        class_id = int(session.get('class_id'))
    else:
        class_id = None
    included = session.get('included')
    all_students = get_all(id)
    if prep_data:
        previous_name = prep_data[1]

    mydb = connect_DB()
    cursor = mydb.cursor()

    if all_students is not None:
        # if class_id exists, check which students are already inrolled in that class
        if prep_data is None:
            available = all_students
        # Otherwise, a new class won't have any included students
        else:
            result = list(set(all_students) - set(included))
            if included is None:
                included = []
            if result is not None:
                available = result

    if request.method == "POST":

        # Collect Form data

        class_name = request.form.get('class_name')
        sun = request.form.get('sunday')
        mon = request.form.get('monday')
        tue = request.form.get('tuesday')
        wed = request.form.get('wednesday')
        thu = request.form.get('thursday')
        fri = request.form.get('friday')
        sat = request.form.get('saturday')

        # Transforms checkbox values into boolean
        if sun:
            sun = 1
        else:
            sun = 0
        if mon:
            mon = 1
        else:
            mon = 0
        if tue:
            tue = 1
        else:
            tue = 0
        if wed:
            wed = 1
        else:
            wed = 0
        if thu:
            thu = 1
        else:
            thu = 0
        if fri:
            fri = 1
        else:
            fri = 0
        if sat:
            sat = 1
        else:
            sat = 0

        date_start = request.form.get('date_start')
        date_end = request.form.get('date_end')
        time_start = request.form.get('time_start')
        time_end = request.form.get('time_end')
        status = check_status(date_start, date_end)
        data = (class_name, sun, mon, tue, wed, thu, fri, sat, date_start, date_end, time_start, time_end, status, id)
        enrolledlist = request.form.getlist('enrolledlist')

        class_dates = create_class_dates(date_start, date_end, sun, mon, tue, wed, thu, fri, sat)

        enrolled = []
        for u in enrolledlist:
            value = u.split("-")
            enrolled.append((int(value[0]), value[1]))

        # Persist form data, so it won't have to be filled out again
        # Time is usually built in JS into a single variable, then sent to DB.
        # From server to HTML, it is always split back into 3 parts in JS.
        # Because this data is never sent to DB, it is redundantly converted to DB format(without sending it)
        # and back to form format in JS.
        tsp = request.form.get("start_hour") + ":" + request.form.get("start_minute") + " " + request.form.get(
            "start_period")
        tep = request.form.get("end_hour") + ":" + request.form.get("end_minute") + " " + request.form.get("end_period")
        prep_data = (None, class_name, sun, mon, tue, wed, thu, fri, sat, date_start, date_end, tsp, tep, 2)
        session['prep_data'] = prep_data
        session['included'] = enrolled
        student_name = request.form.get('student_name')

        # if 'quickadd' in request.form:
        if student_name != "":

            names = student_name.split(",")
            names[0].strip()
            names[1].strip()
            name_last = names[0].replace(' ', '')
            name_first = names[1].replace(' ', '')

            # Check if name already exists
            statement = "SELECT EXISTS (SELECT * FROM student WHERE name_last = %s AND name_first = %s"
            statement += " AND owner = %s)"
            try:
                cursor.execute(statement, (name_last, name_first, id))
                exists = cursor.fetchone()
            except:
                flash("Database error checking if name already exists")
                return redirect(url_for('error'))

            if exists[0] == 0:
                session['student_exists'] = None
                cursor.execute(
                    "INSERT INTO student (name_last,name_first,phone_number,email,owner) VALUES (%s, %s, %s, %s, %s)",
                    (name_last, name_first, "", "", id))
                mydb.commit()
                cursor.execute("SELECT LAST_INSERT_ID()")
                res_new_id = cursor.fetchone()
                new_student = (str(res_new_id[0]), student_name)
                enrolled.append(new_student)
                session['included'] = enrolled
                return render_template('editclass.html', message=session.get('class_exists'),
                                       overlap=session.get('overlap'), hour_list=h, minute_list=m, avail=available,
                                       inc=session.get('included'), pre=prep_data,
                                       student_exists=session.get('student_exists'))
            else:
                # If student name already exists, reload and send a warning message
                session['student_exists'] = "Name already in use"
                return redirect(url_for('editclass'))

        if 'save' in request.form:

            # First, Let's check conflicts before recording any data

            # Check overlapping time and date conflicts with other classes
            session['overlap'] = check_schedule_overlap(sun, mon, tue, wed, thu, fri, sat, time_start, time_end,
                                                        date_start, date_end, class_id)
            if session.get('overlap') is None:

                if class_id is None:

                    # Check if class name already exists
                    cursor.execute("SELECT EXISTS (SELECT * FROM class WHERE name = %s and owner = %s)",
                                   (class_name, id))
                    exists = cursor.fetchone()
                    if exists[0] == 0:
                        session['class_exists'] = None

                        # Creating new class
                        statement = "INSERT INTO class (name,sun,mon,tue,wed,thu,fri,sat,"
                        statement += "date_start,date_end,time_start,time_end,status,owner) VALUES "
                        statement += "(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
                        cursor.execute(statement, (data))

                        # First fetch the new class id
                        cursor.execute("SELECT LAST_INSERT_ID()")
                        last_res = cursor.fetchone()
                        class_id = last_res[0]

                        # Enrolling Students
                        for e in enrolled:
                            cursor.execute("INSERT INTO enrollment (student_id, class_id) VALUES (%s,%s)",
                                           (e[0], class_id))

                        # Creating dates for class
                        for i in class_dates:
                            cursor.execute("INSERT INTO class_dates (class_id, date) VALUES (%s,%s)", (class_id, i))

                        # It seems I only have to commit once both info and students have been sent to DB
                        try:
                            mydb.commit()
                        except:
                            flash("Error committing changes to database")
                            return redirect(url_for('error'))
                        return redirect(url_for('classes'))
                    else:
                        # If class name already exists, reload and send a warning message
                        session['class_exists'] = "Class Name already in use"
                        return redirect(url_for('editclass'))

                else:
                    # Check if class name already exists
                    cursor.execute("SELECT EXISTS (SELECT * FROM class WHERE name = %s and owner = %s)",
                                   (class_name, id))
                    exists = cursor.fetchone()
                    # In update, if a new name is entered, it will updade if new name does not exist or 
                    # if it is the same it was before
                    if exists[0] == 0 or (exists[0] == 1 and class_name == previous_name):
                        session['class_exists'] = None
                        status = check_status(date_start, date_end)
                        update_statement = "UPDATE class SET name=%s,sun=%s,mon=%s,tue=%s,wed=%s,thu=%s,fri=%s,"
                        update_statement += "sat=%s,date_start=%s,date_end=%s,time_start=%s,time_end=%s,status=%s WHERE id = %s"
                        data2 = (class_name, sun, mon, tue, wed, thu, fri, sat, date_start, date_end, time_start,
                                 time_end, status, class_id)
                        cursor.execute(update_statement, (data2))

                        """
                        # Delete and re-enroll students in enrollment DB
                        cursor.execute("DELETE FROM enrollment WHERE class_id = %s",(class_id,))
                        for e in enrolled:
                            cursor.execute("INSERT INTO enrollment (student_id, class_id) VALUES (%s,%s)", (e[0],class_id))
                        """

                        # Delete students from enrollment which were dropped, and add new students
                        remove = []
                        enroll = []
                        statement_remove = "DELETE FROM enrollment WHERE student_id = %s"
                        statement_enroll = "INSERT IGNORE INTO enrollment (student_id, class_id) VALUES (%s,%s)"

                        # First remove items from included that were not selected in enrolledlist
                        if not included is None:  # In case there are no students enrolled when updating
                            for i in included:
                                if not (i in enrolled):
                                    remove.append((i[0],))
                        try:
                            cursor.executemany(statement_remove, (remove))
                        except:
                            flash("Error deleting students from enrollment")
                            return redirect(url_for('error'))

                        # Then add new students to included, ignore any repetitions
                        for e in enrolled:
                            enroll.append((e[0], class_id))
                        try:
                            cursor.executemany(statement_enroll, (enroll))
                        except:
                            flash("Error updating new enrolled students")
                            return redirect(url_for('error'))

                        # Remove dates which were dropped and add new dates to class_dates
                        # Remove dates
                        remove_dates = []
                        remove_statement = "DELETE FROM class_dates WHERE class_id = %s AND date = %s"
                        cds = session.get('class_dates')
                        for c in cds:
                            if not c[0] in class_dates:
                                remove_dates.append((class_id, c[0]))
                        try:
                            cursor.executemany(remove_statement, (remove_dates))
                        except:
                            flash("Error removing/updating class_dates #1")
                            return redirect(url_for('error'))

                        # Add dates
                        add_dates = []
                        for cd in class_dates:
                            add_dates.append((class_id, cd))
                        add_statement = "INSERT IGNORE INTO class_dates (class_id, date) VALUES (%s,%s)"
                        try:
                            cursor.executemany(add_statement, (add_dates))
                        except:
                            flash("Error adding/updating class_dates #2")
                            return redirect(url_for('error'))
                        mydb.commit()
                        return redirect(url_for('classinfo'))
                    else:
                        # If class name already exists, reload and send a warning message
                        session['class_exists'] = "Class Name already in use"
                        return redirect(url_for('editclass'))
            else:
                # if there is schedule overlap, reload and send a warning message
                return redirect(url_for('editclass'))

    return render_template('editclass.html', message=session.get('class_exists'),
                           overlap=session.get('overlap'), hour_list=h, minute_list=m, avail=available,
                           inc=session.get('included'), pre=prep_data, student_exists=session.get('student_exists'))


def create_class_dates(date_start, date_end, su, mo, tu, we, th, fr, sa):
    # start = datetime.date(date_start)
    # end = datetime.date(date_end)
    start = datetime.strptime(date_start, '%Y-%m-%d')
    end = datetime.strptime(date_end, '%Y-%m-%d')
    dates = []
    for i in range(int((end - start).days) + 1):
        # yield start + timedelta(i)
        day = start + timedelta(i)
        if day.isoweekday() == 7:
            if su:
                dates.append(day.strftime('%Y-%m-%d'))
        elif day.isoweekday() == 1:
            if mo:
                dates.append(day.strftime('%Y-%m-%d'))
        elif day.isoweekday() == 2:
            if tu:
                dates.append(day.strftime('%Y-%m-%d'))
        elif day.isoweekday() == 3:
            if we:
                dates.append(day.strftime('%Y-%m-%d'))
        elif day.isoweekday() == 4:
            if th:
                dates.append(day.strftime('%Y-%m-%d'))
        elif day.isoweekday() == 5:
            if fr:
                dates.append(day.strftime('%Y-%m-%d'))
        elif day.isoweekday() == 6:
            if sa:
                dates.append(day.strftime('%Y-%m-%d'))
    return dates


def delete_class(class_id):
    # mysql DB is set up so entries are deleted for any foreign keys that reference a parent table. i.e. 
    # If a delete class, all entries in enrollment where class_id match, will be deleted
    # Delete class from the DB will automatically delete class_dates, enrollment, and attendance.
    mydb = None
    cursor = None
    try:
        mydb = connect_DB()
        cursor = mydb.cursor()
        cursor.execute("DELETE FROM class WHERE id = %s", (class_id,))
        mydb.commit()
    except:
        flash("Error deleting class!")
        return redirect(url_for('error'))


def check_schedule_overlap(su, mo, tu, we, th, fr, sa, ts, te, ds, de, class_id):
    if su:
        weekday = "sun"
    elif mo:
        weekday = "mon"
    elif tu:
        weekday = "tue"
    elif we:
        weekday = "wed"
    elif th:
        weekday = "thu"
    elif fr:
        weekday = "fri"
    else:
        weekday = "sat"

    try:
        mydb = connect_DB()
        cursor = mydb.cursor()
    except:
        flash("Error connecting to database")
        return redirect(url_for('error'))
    # query to collect class info
    try:
        # First query searches for classes in the date range and the first same day of the week
        query = "SELECT DISTINCT class_id FROM class_dates WHERE date > %s AND date < %s AND (class_id IN ("
        query += "SELECT id FROM class WHERE owner = %s AND "
        query += weekday
        query += " = 1))"
        cursor.execute(query, (ds, de, session.get('id'),))
        res = cursor.fetchall()
        # ----------------------------------------------------------------------------------
        # The class that is being checked should not conflict with itself in case it is being updated
        # We should exclude it from the results if they come up
        if class_id != None:
            same = (class_id,)
            if same in res:
                res.remove(same)
        # ----------------------------------------------------------------------------------
        # Second query checks if new class times overlap either in the beginning, end or within 
        # pre-existing times
        time_query = "SELECT name FROM class WHERE id = %s AND ((%s < time_start AND %s > time_start) OR "
        time_query += "(%s < time_end AND %s > time_end) OR (%s > time_start AND %s < time_end))"
        matches = []  # This list will hold any conflicting classes
        flag = False  # This flag will tell if there are any conflicting classes
        # Let's loop the results and add matches to list, turn flag on if there is a single match
        for r in res:
            cursor.execute(time_query, (r[0], ts, te, ts, te, ts, te,))
            match = cursor.fetchone()
            if match != None:
                matches.append(match[0])
                flag = True
        if flag:
            return matches
    except:
        flash("Error getting schedule overlaps")
        return redirect(url_for('error'))

    return None


def check_status(date_start, date_end):
    today = datetime.today()
    start = datetime.strptime(date_start, '%Y-%m-%d')
    end = datetime.strptime(date_end, '%Y-%m-%d')
    if start > today:
        return 1
    if end < today:
        return 2
    if start <= today and end >= today:
        return 0
