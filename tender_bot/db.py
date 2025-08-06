import psycopg2
import threading
from tender_bot.config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD, USE_MOCK_DB
from tender_bot.models import CREATE_TABLES_SQL

class Database:
    """Класс для работы с базой данных PostgreSQL."""
    def __init__(self):
        self.conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        print("Подключено к PostgreSQL")

    def execute(self, sql, params=None, fetch=None):
        with self.conn.cursor() as cur:
            cur.execute(sql, params)
            if fetch == 'one':
                return cur.fetchone()
            if fetch == 'all':
                return cur.fetchall()
            self.conn.commit()

    def init_db(self):
        print("Инициализация таблиц в PostgreSQL...")
        self.execute(CREATE_TABLES_SQL)
        print("Таблицы созданы.")

class MockDatabase:
    """
    Класс-заглушка для базы данных, хранящий данные в памяти.
    Полезен для тестирования и разработки без PostgreSQL.
    """
    def __init__(self):
        self._users = []
        self._applications = []
        self._files = []
        self._deals = []
        self._status_log = []
        self._messages_log = []
        self._next_user_id = 1
        self._next_app_id = 1
        self._next_deal_id = 1
        self.lock = threading.Lock()
        print("Используется Mock база данных (in-memory)")

    def init_db(self):
        print("Инициализация Mock базы данных (пропущено).")
        pass

    def execute(self, sql, params=None, fetch=None):
        # Эта заглушка не выполняет SQL, а имитирует его поведение
        # на основе заранее определенных методов.
        # Для реального мокирования SQL можно было бы использовать sqlite :memory:
        print(f"Mock Execute (fetch={fetch}): {sql[:50]}... with params {params}")
        
        # Простая и неполная имитация. Для тестов достаточно.
        if "INSERT INTO users" in sql:
            with self.lock:
                telegram_id = params[0]
                if not any(u['telegram_id'] == telegram_id for u in self._users):
                    user = {'id': self._next_user_id, 'telegram_id': params[0], 'username': params[1], 'role': params[2]}
                    self._users.append(user)
                    self._next_user_id += 1
        
        if "SELECT id FROM users WHERE telegram_id" in sql:
             with self.lock:
                user = next((u for u in self._users if u['telegram_id'] == params[0]), None)
                if fetch == 'one':
                    return (user['id'],) if user else None
        
        if "INSERT INTO applications" in sql:
             with self.lock:
                app = {'id': self._next_app_id, 'client_id': params[0], 'company_name': params[1], 'contact_name': params[2], 'description': params[3], 'status': 'new'}
                self._applications.append(app)
                if fetch == 'one':
                    return (self._next_app_id,)
                self._next_app_id += 1
        
        # Добавьте другие имитации по мере необходимости...
        
        if fetch == 'one':
            return None
        if fetch == 'all':
            return []

# Создаем глобальный объект для доступа к базе данных
# The global 'db' object that will be used throughout the application
db = None

def init_database():
    """
    Инициализирует подключение к базе данных в зависимости от конфигурации.
    """
    global db
    if USE_MOCK_DB:
        # Для тестирования и локальной разработки без Docker/Postgres.
        # Чтобы использовать PostgreSQL, установите USE_MOCK_DB в False в config.py.
        db = MockDatabase()
    else:
        # Для полноценной работы с PostgreSQL.
        # Убедитесь, что у вас запущен PostgreSQL и правильно указаны
        # креды в config.py.
        try:
            db = Database()
        except psycopg2.OperationalError as e:
            print(f"ОШИБКА: Не удалось подключиться к PostgreSQL. {e}")
            print("Пожалуйста, проверьте настройки в config.py и убедитесь, что база данных запущена.")
            exit(1)
            
    db.init_db()