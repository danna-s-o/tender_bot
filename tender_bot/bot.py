import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters, CallbackQueryHandler
from config import BOT_TOKEN
from db import init_db, register_user
from handlers.client import (
    start_application, ask_company, ask_contact, ask_description, ask_docs, ask_images, ask_comments, confirm,
    ASK_COMPANY, ASK_CONTACT, ASK_DESCRIPTION, ASK_DOCS, ASK_IMAGES, ASK_COMMENTS, CONFIRM
)
from handlers.admin import list_applications, application_detail, assign_executor
from handlers.executor import list_deals, change_status, set_status
from filters import is_contact_info, log_message

logging.basicConfig(level=logging.INFO)

CHOOSE_ROLE = 1
ROLES = ["Клиент", "Исполнитель", "Администратор"]
ROLE_MAP = {"Клиент": "client", "Исполнитель": "executor", "Администратор": "admin"}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    keyboard = [[KeyboardButton(role)] for role in ROLES]
    await update.message.reply_text(
        "Добро пожаловать! Пожалуйста, выберите вашу роль:",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return CHOOSE_ROLE

async def choose_role(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    role_text = update.message.text
    role = ROLE_MAP.get(role_text)
    if not role:
        await update.message.reply_text("Пожалуйста, выберите роль с помощью кнопок.")
        return CHOOSE_ROLE
    register_user(user.id, user.username, role)
    await update.message.reply_text(f"Вы зарегистрированы как {role_text}.")
    return ConversationHandler.END

async def group_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    # Определяем id сделки по chat_id (здесь предполагается, что chat_id = deal_id + OFFSET, либо нужен маппинг)
    # Для MVP можно не связывать, а просто логировать сообщения
    deal_id = chat.id  # Для реального проекта нужен маппинг chat_id <-> deal_id
    if message.text and is_contact_info(message.text):
        await message.delete()
        await message.reply_text('Контактные данные запрещены! Сообщение удалено.')
        log_message(deal_id, user.id, message.text, is_deleted=True, reason='contact_info')
    else:
        log_message(deal_id, user.id, message.text or '', is_deleted=False)

def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSE_ROLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_role)]
        },
        fallbacks=[]
    )
    app.add_handler(conv_handler)

    # ConversationHandler для подачи заявки клиентом
    client_application_handler = ConversationHandler(
        entry_points=[CommandHandler('new_application', start_application)],
        states={
            ASK_COMPANY: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_company)],
            ASK_CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_contact)],
            ASK_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_description)],
            ASK_DOCS: [
                MessageHandler(filters.Document.ALL, ask_docs),
                MessageHandler(filters.TEXT & ~filters.COMMAND, ask_docs)
            ],
            ASK_IMAGES: [
                MessageHandler(filters.PHOTO, ask_images),
                MessageHandler(filters.TEXT & ~filters.COMMAND, ask_images)
            ],
            ASK_COMMENTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_comments)],
            CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm)]
        },
        fallbacks=[],
        allow_reentry=True
    )
    app.add_handler(client_application_handler)

    # Админ-команды
    app.add_handler(CommandHandler('admin_applications', list_applications))
    app.add_handler(CallbackQueryHandler(application_detail, pattern=r'^app_detail_\d+$'))
    app.add_handler(CallbackQueryHandler(assign_executor, pattern=r'^assign_\d+_\d+$'))

    # Команды исполнителя
    app.add_handler(CommandHandler('my_deals', list_deals))
    app.add_handler(CommandHandler('status', change_status))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, set_status))

    # Групповые чаты: фильтрация и логирование
    app.add_handler(MessageHandler(filters.ChatType.GROUPS & filters.TEXT, group_message_handler))

    app.run_polling()

if __name__ == '__main__':
    main()