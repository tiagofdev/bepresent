from flask import Flask, render_template, request, Response, redirect, url_for, flash, session
import datetime
from datetime import date
import time
import json
import calendar
from mysql_db import connect_DB

wd = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"]

def show_calendar(id):
    
    session['today'] = datetime.date.today()
    today = session.get('today')
    
    if session.get('month') is None:
        session['month'] = int(today.strftime("%m"))
    if session.get('year') is None:
        session['year'] = int(today.strftime("%y"))
        session['year'] += 2000

    month = session.get('month')
    year = session.get('year')
    month_data = None

    fwd = get_first_weekday(month, year)
    dm = get_days_in_month(month, year)
    month_data = get_month_data(month, year, id)
    date_now = datetime.datetime.now()
    js_date = json.dumps((time.mktime(date_now.timetuple())) * 1000)
    
    if request.method == "POST":
        class_id = request.form.get('class_id')
        session['class_id'] = class_id
        date = request.form.get('date')
        
        if 'button_next' in request.form:
            month_c = int(request.form.get('month'))
            year_c = int(request.form.get('year'))
            month_p = 0
            year_p = 0
            if (month_c == 12):
                month_p = 1
                year_p = year_c + 1
            else:
                month_p = month_c + 1
                year_p = year_c
            session['month'] = month_p
            session['year'] = year_p
            month = session.get('month')
            year = session.get('year')
            
            return redirect(url_for('calendar'))

        elif 'button_previous' in request.form:
            month_c = int(request.form.get('month'))
            year_c = int(request.form.get('year'))
            month_p = 0
            year_p = 0
            if (month_c == 1):
                month_p = 12
                year_p = year_c - 1
            else:
                month_p = month_c - 1
                year_p = year_c
            session['month'] = month_p
            session['year'] = year_p
            month = session.get('month')
            year = session.get('year')
            return redirect(url_for('calendar'))
        elif 'button_attendance' in request.form:
            session['atten_date'] = date
            return redirect(url_for('attendance'))
        elif 'button_class' in request.form:
            return redirect(url_for('classinfo'))
        
    return render_template('calendar.html', weekdays=wd, days_in_month=dm, first_weekday = fwd, js_date = js_date,
        month=month, year=year, month_data=month_data)

def get_month_data(month_p, year_p, id_p):
    date_start = date(year_p, month_p, 1)
    date_end = date(year_p, month_p, get_days_in_month(month_p, year_p))
    try:
        mydb = connect_DB()
        cursor = mydb.cursor()
    except:
        flash("Error connecting to database")
        return redirect(url_for('error'))
    try:
        qcd = "SELECT id, name, "
        qcd += "CONCAT_WS(' - ',DATE_FORMAT(time_start,'%H:%i'),DATE_FORMAT(time_end,'%H:%i')) AS time, "
        qcd += "DATE_FORMAT(date,'%Y-%m-%d') "
        qcd += "FROM class "
        qcd += "INNER JOIN class_dates "
        qcd += "ON class.id = class_dates.class_id "
        qcd += "WHERE date >= %s AND date <= %s AND owner = %s"
        qcd += "ORDER BY date"
        cursor.execute(qcd, (date_start, date_end, id_p))
        month_data = cursor.fetchall()
    except:
        flash("Error retrieving classes data")
        return redirect(url_for('error'))
    return month_data
    
def get_days_in_month(month_p, year_p):
    
    jmm = [1, 3, 5, 7, 8, 10, 12]
    ajs = [4, 6, 9, 11]
    if month_p in jmm:
        return 31
    elif month_p in ajs:
        return 30
    else:
        if is_leap_year(year_p):
            return 29
        else:
            return 28

def is_leap_year(year_p):
    return calendar.isleap(year_p)

def get_first_weekday(month_p,year_p):
    firstday = calendar.weekday(year_p, month_p, 1)
    if firstday == 6:
        firstday = -1
    return firstday