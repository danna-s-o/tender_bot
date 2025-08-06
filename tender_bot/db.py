import psycopg2
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
from models import CREATE_TABLES_SQL

def get_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(CREATE_TABLES_SQL)
    conn.commit()
    cur.close()
    conn.close()

def register_user(telegram_id, username, role):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO users (telegram_id, username, role)
        VALUES (%s, %s, %s)
        ON CONFLICT (telegram_id) DO NOTHING;
        """,
        (telegram_id, username, role)
    )
    conn.commit()
    cur.close()
    conn.close()