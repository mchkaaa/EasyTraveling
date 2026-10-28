import os
import smtplib
import random
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

def generate_otp():
    """Генерує випадковий 6-значний код"""
    return str(random.randint(100000, 999999))

def send_otp_email(receiver_email, otp_code):
    """Відправляє лист із кодом на вказаний email"""
    sender_email = os.getenv("EMAIL_SENDER")
    password = os.getenv("EMAIL_PASSWORD")

    if not sender_email or not password:
        print("Помилка: Не налаштовані EMAIL_SENDER або EMAIL_PASSWORD")
        return False

    subject = "Код підтвердження EasyTraveling"
    body = f"Вітаємо!\n\nВаш код підтвердження для завершення реєстрації: {otp_code}\n\nНікому його не повідомляйте."
    
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = f"EasyTraveling <{sender_email}>"
    msg['To'] = receiver_email

    try:
        # Підключаємося до сервера Google
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, password)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Помилка відправки листа: {e}")
        return False