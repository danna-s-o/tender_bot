import re
from db import get_connection

def is_contact_info(text):
    # Поиск телефонов, email, ссылок на мессенджеры
    phone_pattern = r"(\+?\d[\d\-\s]{7,}\d)"
    email_pattern = r"[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}"
    messenger_pattern = r"(t\.me/|@\w{4,}|whatsapp|wa\.me/|viber|vk\.me/|telegram\.me/)"
    url_pattern = r"https?://[\w\.-]+"
    patterns = [phone_pattern, email_pattern, messenger_pattern, url_pattern]
    for pat in patterns:
        if re.search(pat, text, re.IGNORECASE):
            return True
    return False

def log_message(deal_id, sender_id, message, is_deleted=False, reason=None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO messages_log (deal_id, sender_id, message, is_deleted, reason) VALUES (%s, %s, %s, %s, %s)",
        (deal_id, sender_id, message, is_deleted, reason)
    )
    conn.commit()
    cur.close()
    conn.close()