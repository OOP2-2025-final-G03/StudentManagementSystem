from sqlite3 import SqliteDatabase, connect, Row

# メインデータベース接続
db = SqliteDatabase('database.db')

DB_PATH = "database.db"

def get_db_connection():
    conn = connect(DB_PATH)
    conn.row_factory = Row
    return conn