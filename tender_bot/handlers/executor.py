from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from tender_bot.db import db
import requests
from datetime import datetime
from tender_bot.config import API_624_URL, API_624_TOKEN

# Предлагаемые статусы
DEAL_STATUSES = [
    ("В работе", "in_progress"),
    ("Требуется информация", "need_info"),
    ("На проверке", "on_review"),
    ("Завершена", "done"),
    ("Отменена", "cancelled")
]

async def list_deals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    rows = db.execute("SELECT d.id, a.company_name, a.description, d.status FROM deals d JOIN applications a ON d.application_id = a.id WHERE d.executor_id = (SELECT id FROM users WHERE telegram_id = %s)", (user.id,), fetch='all')
    if not rows:
        await update.message.reply_text('У вас нет назначенных сделок.')
        return
    for row in rows:
        deal_id, company, desc, status = row
        await update.message.reply_text(f"Сделка #{deal_id}\nКомпания: {company}\nОписание: {desc}\nСтатус: {status}")

async def change_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args
    if not args or not args[0].isdigit():
        await update.message.reply_text('Используйте: /status <id_сделки>')
        return
    deal_id = int(args[0])
    keyboard = [[status[0]] for status in DEAL_STATUSES]
    context.user_data['deal_id'] = deal_id
    await update.message.reply_text('Выберите новый статус:', reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True))

async def set_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    deal_id = context.user_data.get('deal_id')
    status_text = update.message.text
    status_code = None
    for ru, code in DEAL_STATUSES:
        if status_text == ru:
            status_code = code
            break
    if not status_code:
        await update.message.reply_text('Пожалуйста, выберите статус с помощью кнопок.')
        return
    # Обновить статус в БД
    db.execute("UPDATE deals SET status = %s, updated_at = NOW() WHERE id = %s", (status_code, deal_id))
    db.execute("INSERT INTO deal_status_log (deal_id, status, changed_by) VALUES (%s, %s, (SELECT id FROM users WHERE telegram_id = %s))", (deal_id, status_code, user.id))
    
    # Получить username исполнителя для экспорта
    executor_username = db.execute("SELECT username FROM users WHERE telegram_id = %s", (user.id,), fetch='one')[0]
    
    # Экспортировать статус в 624
    export_status_624(deal_id, status_code, executor_username)
    await update.message.reply_text(f'Статус сделки #{deal_id} обновлён на "{status_text}".')

    # TODO: Отправить уведомление клиенту о смене статуса

def export_status_624(deal_id, status, executor_username):
    payload = {
        "deal_id": str(deal_id),
        "status": status,
        "executor_id": executor_username, # Используем username, как в ТЗ
        "timestamp": datetime.utcnow().isoformat()
    }
    headers = {"Authorization": f"Bearer {API_624_TOKEN}"}
    try:
        # Раскомментируйте для реальной отправки
        # response = requests.post(API_624_URL, json=payload, headers=headers, timeout=10)
        # response.raise_for_status()
        # print(f"Статус сделки {deal_id} успешно экспортирован в 624. Ответ: {response.status_code}")
        
        # Заглушка для лога
        print(f"MOCK EXPORT: Отправка в 624. URL: {API_624_URL}, Payload: {payload}")

    except requests.exceptions.RequestException as e:
        print(f"ОШИБКА: Не удалось экспортировать статус сделки {deal_id} в систему 624. {e}")