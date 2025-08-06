from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from db import get_connection

async def list_applications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT a.id, u.username, a.company_name, a.status FROM applications a JOIN users u ON a.client_id = u.id WHERE a.status = 'new'")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    if not rows:
        await update.message.reply_text('Нет новых заявок.')
        return
    for row in rows:
        app_id, username, company, status = row
        await update.message.reply_text(
            f"Заявка #{app_id}\nКлиент: @{username}\nКомпания: {company}\nСтатус: {status}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton('Подробнее', callback_data=f'app_detail_{app_id}')]
            ])
        )

async def application_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    app_id = int(query.data.split('_')[-1])
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT a.id, u.username, a.company_name, a.contact_name, a.description, a.status FROM applications a JOIN users u ON a.client_id = u.id WHERE a.id = %s", (app_id,))
    app = cur.fetchone()
    cur.execute("SELECT file_type, file_path FROM files WHERE application_id = %s", (app_id,))
    files = cur.fetchall()
    cur.close()
    conn.close()
    if not app:
        await query.edit_message_text('Заявка не найдена.')
        return
    app_id, username, company, contact, desc, status = app
    text = f"Заявка #{app_id}\nКлиент: @{username}\nКомпания: {company}\nКонтакт: {contact}\nОписание: {desc}\nСтатус: {status}"
    if files:
        text += "\nФайлы:"
        for ftype, fpath in files:
            text += f"\n- [{ftype}] {fpath}"
    # Кнопка "Назначить исполнителя"
    text += "\n\nНазначить исполнителя:"
    # Получаем список исполнителей
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, username FROM users WHERE role = 'executor'")
    executors = cur.fetchall()
    cur.close()
    conn.close()
    buttons = [[InlineKeyboardButton(f"@{ex[1]}", callback_data=f'assign_{app_id}_{ex[0]}')] for ex in executors]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons))

async def assign_executor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _, app_id, executor_id = query.data.split('_')
    app_id = int(app_id)
    executor_id = int(executor_id)
    # Создать сделку и обновить статус заявки
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO deals (application_id, executor_id, status) VALUES (%s, %s, 'new') RETURNING id", (app_id, executor_id))
    deal_id = cur.fetchone()[0]
    cur.execute("UPDATE applications SET status = 'assigned' WHERE id = %s", (app_id,))
    conn.commit()
    cur.close()
    conn.close()
    await query.edit_message_text(f'Исполнитель назначен. Сделка #{deal_id} создана.')