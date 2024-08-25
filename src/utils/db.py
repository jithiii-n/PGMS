# utils/db.py

import pymysql
from flask import current_app

def get_db_connection():
    config = current_app.config['DATABASE']
    return pymysql.connect(
        host=config['host'],
        port=config['port'],
        user=config['user'],
        password=config['password'],
        db=config['db'],
        cursorclass=pymysql.cursors.DictCursor
    )

def iud(query, values):
    try:
        con = get_db_connection()
        with con.cursor() as cmd:
            cmd.execute(query, values)
            id = cmd.lastrowid
            con.commit()
    except Exception as e:
        print(f"Database error: {e}")
        id = None
    finally:
        con.close()
    return id
def selectone(query, values):
    """Select a single record"""
    try:
        con = get_db_connection()
        with con.cursor() as cursor:
            cursor.execute(query, values)
            result = cursor.fetchone()
    except Exception as e:
        print(f"Database error: {e}")
        result = None
    finally:
        con.close()
    return result

def select_all(query, values):
    """Select multiple records"""
    try:
        con = get_db_connection()
        with con.cursor() as cursor:
            cursor.execute(query, values)
            results = cursor.fetchall()
    except Exception as e:
        print(f"Database error: {e}")
        results = []
    finally:
        con.close()
    return results

def update(query, values):
    """Update operations"""
    try:
        con = get_db_connection()
        with con.cursor() as cursor:
            cursor.execute(query, values)
            con.commit()
    except Exception as e:
        print(f"Database error: {e}")
    finally:
        con.close()
