# extensions.py
from flask_mysqldb import MySQL
from MySQLdb.cursors import DictCursor


mysql = MySQL()

def init_db(app):
    """
    Initializes the MySQL object with the Flask application.
    This function should be called from your main app.py file.
    """
    mysql.init_app(app)