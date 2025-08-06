"""
SQL-скрипт для создания структуры базы данных PostgreSQL для тендерного бота.
"""

CREATE_TABLES_SQL = """
-- Пользователи
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username TEXT,
    role VARCHAR(20) NOT NULL, -- client, executor, admin
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Заявки (от клиентов)
CREATE TABLE IF NOT EXISTS applications (
    id SERIAL PRIMARY KEY,
    client_id INTEGER REFERENCES users(id),
    company_name TEXT NOT NULL,
    contact_name TEXT NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'new',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Файлы, прикрепленные к заявкам
CREATE TABLE IF NOT EXISTS files (
    id SERIAL PRIMARY KEY,
    application_id INTEGER REFERENCES applications(id),
    file_type VARCHAR(10), -- doc, pdf, xls, img и т.д.
    file_path TEXT NOT NULL,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Сделки (назначение исполнителя)
CREATE TABLE IF NOT EXISTS deals (
    id SERIAL PRIMARY KEY,
    application_id INTEGER REFERENCES applications(id),
    executor_id INTEGER REFERENCES users(id),
    status VARCHAR(20) DEFAULT 'new',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Лог смены статусов сделки
CREATE TABLE IF NOT EXISTS deal_status_log (
    id SERIAL PRIMARY KEY,
    deal_id INTEGER REFERENCES deals(id),
    status VARCHAR(20) NOT NULL,
    changed_by INTEGER REFERENCES users(id),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Лог сообщений в чате сделки
CREATE TABLE IF NOT EXISTS messages_log (
    id SERIAL PRIMARY KEY,
    deal_id INTEGER REFERENCES deals(id),
    sender_id INTEGER REFERENCES users(id),
    message TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    reason TEXT
);

-- Уведомления для администратора
CREATE TABLE IF NOT EXISTS admin_notifications (
    id SERIAL PRIMARY KEY,
    type VARCHAR(30),
    data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""