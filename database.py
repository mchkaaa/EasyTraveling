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
    

    # Створюємо таблицю для подорожей
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            destination TEXT NOT NULL,
            start_date TEXT,
            end_date TEXT,
            notes TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
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

def verify_user(email, password):
    """Шукає користувача і перевіряє правильність пароля"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Шукаємо запис за email
    cursor.execute("SELECT id, password_hash FROM users WHERE email = ?", (email,))
    user_record = cursor.fetchone() # fetchone() дістає рівно один знайдений рядок
    
    conn.close() # Закриваємо двері до бази, бо дані ми вже дістали
    
    # Якщо такого email немає в базі
    if user_record is None:
        return None
        
    # user_record виглядає як кортеж: (id, "зашифрований_пароль")
    user_id = user_record[0]
    db_password_hash = user_record[1]
    
    # Перевіряємо, чи введений пароль відповідає шифру з бази
    if check_password_hash(db_password_hash, password):
        return user_id  # Успіх! Повертаємо id користувача
    else:
        return None     # Пароль не підійшов