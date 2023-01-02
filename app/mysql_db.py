import mysql.connector

# Connecting to the database
def connect_DB():
    conn = mysql.connector.connect(
        # user="root",
        # password="",
        # host="127.0.0.1",
        user="tiago",
        password="atg+d4.efckiI&TS",
        # host="35.196.75.81", public
        host="10.86.32.3",  # private connection
        port="3306",
        database="attendb"
        )

    return conn

# Disconnect the database
def disconnect_DB(cursor, connection):
    cursor.close()
    connection.close()
