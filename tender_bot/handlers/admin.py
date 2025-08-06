from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from tender_bot.db import db

async def list_applications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = db.execute("SELECT a.id, u.username, a.company_name, a.status FROM applications a JOIN users u ON a.client_id = u.id WHERE a.status = 'new'", fetch='all')
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
    
    app = db.execute("SELECT a.id, u.username, a.company_name, a.contact_name, a.description, a.status FROM applications a JOIN users u ON a.client_id = u.id WHERE a.id = %s", (app_id,), fetch='one')
    files = db.execute("SELECT file_type, file_path FROM files WHERE application_id = %s", (app_id,), fetch='all')
    
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
    executors = db.execute("SELECT id, username FROM users WHERE role = 'executor'", fetch='all')
    buttons = [[InlineKeyboardButton(f"@{ex[1]}", callback_data=f'assign_{app_id}_{ex[0]}')] for ex in executors]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons))

async def assign_executor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _, app_id, executor_id = query.data.split('_')
    app_id = int(app_id)
    executor_id = int(executor_id)
    
    # Создать сделку и обновить статус заявки
    deal_id = db.execute("INSERT INTO deals (application_id, executor_id, status) VALUES (%s, %s, 'new') RETURNING id", (app_id, executor_id), fetch='one')[0]
    db.execute("UPDATE applications SET status = 'assigned' WHERE id = %s", (app_id,))
    
    await query.edit_message_text(f'Исполнитель назначен. Сделка #{deal_id} создана.')

    # TODO: Отправить уведомление исполнителю
    # TODO: Отправить уведомление клиенту