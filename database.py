import pyodbc

SERVER = 'localhost'
DATABASE = 'BibliotecaUNII'

CONNECTION_STRING = (
    f'DRIVER={{ODBC Driver 17 for SQL Server}};'
    f'SERVER={SERVER};'
    f'DATABASE={DATABASE};'
    f'Trusted_Connection=yes;'
)

def get_connection():
    return pyodbc.connect(CONNECTION_STRING)