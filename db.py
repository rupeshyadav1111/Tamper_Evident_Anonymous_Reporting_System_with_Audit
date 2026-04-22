import mysql.connector

def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="rupesh11",
        database="reporting_db"
    )
