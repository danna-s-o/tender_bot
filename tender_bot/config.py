BOT_TOKEN = 'ВАШ_ТОКЕН_ТУТ'

# True - использовать Mock (in-memory) базу данных для тестов, False - использовать PostgreSQL
USE_MOCK_DB = True

# Настройки для PostgreSQL (используются, если USE_MOCK_DB = False)
DB_HOST = 'localhost'
DB_PORT = 5432
DB_NAME = 'tenderbot'
DB_USER = 'postgres'
DB_PASSWORD = 'password'

# Настройки для экспорта в систему "624"
API_624_URL = "https://api.624.example.com/deal_status"  # Заменить на реальный URL
API_624_TOKEN = "YOUR_624_TOKEN"  # Заменить на реальный токен