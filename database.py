import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

DB_NAME = "travel.db"

def init_db():
    """Створює таблицю користувачів, якщо її ще немає"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Створюємо таблицю з 4 колонками: id, ім'я, email та зашифрований пароль
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def create_user(name, email, password):
    """Додає нового користувача в базу"""
    hashed_password = generate_password_hash(password) # Шифруємо пароль
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        # Знаки питання (?) захищають базу від хакерських SQL-ін'єкцій
        cursor.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, hashed_password)
        )
        conn.commit()
        return True # Успішно зареєстровано
    except sqlite3.IntegrityError:
        return False # Помилка: такий email вже є в базі (бо ми вказали UNIQUE)
    finally:
        conn.close()