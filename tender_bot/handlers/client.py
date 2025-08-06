from telegram import Update, ReplyKeyboardRemove, Document, PhotoSize
from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, filters, ContextTypes
from tender_bot.db import db
import os

ASK_COMPANY, ASK_CONTACT, ASK_DESCRIPTION, ASK_DOCS, ASK_IMAGES, ASK_COMMENTS, CONFIRM = range(7)

UPLOAD_DIR = 'uploads'
os.makedirs(UPLOAD_DIR, exist_ok=True)

async def start_application(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text('Введите название вашей компании:')
    return ASK_COMPANY

async def ask_company(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['company_name'] = update.message.text.strip()
    await update.message.reply_text('Укажите контактное лицо (только имя):')
    return ASK_CONTACT

async def ask_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['contact_name'] = update.message.text.strip()
    await update.message.reply_text('Опишите ваш тендер:')
    return ASK_DESCRIPTION

async def ask_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['description'] = update.message.text.strip()
    await update.message.reply_text('Загрузите документы (PDF, DOC, DOCX, XLS, XLSX) или отправьте "Пропустить":')
    return ASK_DOCS

async def ask_docs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.document:
        file_id = update.message.document.file_id
        file_name = update.message.document.file_name
        file_path = await save_file(update, context, file_id, file_name)
        context.user_data.setdefault('docs', []).append(file_path)
        await update.message.reply_text('Документ получен. Можете загрузить еще или отправьте "Далее".')
        return ASK_DOCS
    elif update.message.text and update.message.text.lower() == 'далее':
        await update.message.reply_text('Загрузите изображения (JPEG, PNG) или отправьте "Пропустить":')
        return ASK_IMAGES
    elif update.message.text and update.message.text.lower() == 'пропустить':
        await update.message.reply_text('Загрузите изображения (JPEG, PNG) или отправьте "Пропустить":')
        return ASK_IMAGES
    else:
        await update.message.reply_text('Пожалуйста, загрузите документ или отправьте "Далее".')
        return ASK_DOCS

async def ask_images(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        photo: PhotoSize = update.message.photo[-1]
        file_id = photo.file_id
        file_name = f"photo_{file_id}.jpg"
        file_path = await save_file(update, context, file_id, file_name, is_photo=True)
        context.user_data.setdefault('images', []).append(file_path)
        await update.message.reply_text('Изображение получено. Можете загрузить еще или отправьте "Далее".')
        return ASK_IMAGES
    elif update.message.text and update.message.text.lower() == 'далее':
        await update.message.reply_text('Добавьте дополнительные комментарии или отправьте "Нет":')
        return ASK_COMMENTS
    elif update.message.text and update.message.text.lower() == 'пропустить':
        await update.message.reply_text('Добавьте дополнительные комментарии или отправьте "Нет":')
        return ASK_COMMENTS
    else:
        await update.message.reply_text('Пожалуйста, загрузите изображение или отправьте "Далее".')
        return ASK_IMAGES

async def ask_comments(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['comments'] = update.message.text.strip() if update.message.text.lower() != 'нет' else ''
    await update.message.reply_text('Ваша заявка готова к отправке. Подтвердите отправку? (Да/Нет)', reply_markup=ReplyKeyboardRemove())
    return CONFIRM

async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text.lower() == 'да':
        save_application(update, context)
        await update.message.reply_text('Ваша заявка отправлена администратору!')
        return ConversationHandler.END
    else:
        await update.message.reply_text('Заявка отменена.')
        return ConversationHandler.END

async def save_file(update, context, file_id, file_name, is_photo=False):
    bot = context.bot
    file = await bot.get_file(file_id)
    file_path = os.path.join(UPLOAD_DIR, file_name)
    await file.download_to_drive(file_path)
    return file_path

def save_application(update, context):
    user = update.effective_user
    data = context.user_data
    
    # Получаем ID пользователя из нашей БД
    user_db_id = db.execute("SELECT id FROM users WHERE telegram_id = %s", (user.id,), fetch='one')
    if not user_db_id:
        # Этого не должно случиться, если пользователь зарегистрирован
        print(f"ОШИБКА: Пользователь с telegram_id {user.id} не найден в базе.")
        return

    app_id = db.execute(
        """
        INSERT INTO applications (client_id, company_name, contact_name, description, status)
        VALUES (%s, %s, %s, %s, 'new') RETURNING id;
        """,
        (user_db_id[0], data['company_name'], data['contact_name'], data['description']),
        fetch='one'
    )[0]

    # Сохраняем файлы
    for doc_path in data.get('docs', []):
        db.execute(
            "INSERT INTO files (application_id, file_type, file_path) VALUES (%s, %s, %s);",
            (app_id, 'doc', doc_path)
        )
    for img_path in data.get('images', []):
        db.execute(
            "INSERT INTO files (application_id, file_type, file_path) VALUES (%s, %s, %s);",
            (app_id, 'img', img_path)
        )