import flet as ft
import re
from database import create_user, verify_user, check_email_exists
from email_service import generate_otp, send_otp_email

def get_register_view(page: ft.Page):
    # Основні поля
    name_field = ft.TextField(label="Ім'я", width=300, prefix_icon=ft.icons.PERSON)
    email_field = ft.TextField(label="Email", width=300, prefix_icon=ft.icons.EMAIL)
    pass_field = ft.TextField(label="Пароль", width=300, password=True, can_reveal_password=True, prefix_icon=ft.icons.LOCK)
    pass_confirm_field = ft.TextField(label="Підтвердіть пароль", width=300, password=True, can_reveal_password=True, prefix_icon=ft.icons.LOCK_RESET)
    
    # Поле для введення коду (спершу приховане)
    otp_field = ft.TextField(label="Введіть 6-значний код з пошти", width=300, prefix_icon=ft.icons.MARK_EMAIL_READ)
    
    # Змінна для збереження згенерованого коду (використовуємо список для мутабельності всередині функцій)
    current_otp = [""] 
    
    # Групуємо елементи для зручного перемикання видимості
    register_form = ft.Column([name_field, email_field, pass_field, pass_confirm_field], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    
    otp_form = ft.Column([
        ft.Text("Ми відправили код на вашу пошту. Перевірте вхідні (та папку Спам).", text_align=ft.TextAlign.CENTER, color=ft.colors.GREY_400, width=300),
        otp_field,
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, visible=False)

    def verify_otp_click(e):
        otp_field.error_text = None
        # Перевіряємо введений код
        if otp_field.value == current_otp[0]:
            # Якщо код правильний, створюємо користувача в базі
            success = create_user(name_field.value, email_field.value, pass_field.value)
            if success:
                user_id = verify_user(email_field.value, pass_field.value)
                page.client_storage.set("user_id", user_id)
                page.go("/planner")
        else:
            otp_field.error_text = "Неправильний код. Спробуйте ще раз."
        page.update()

    
    verify_btn = ft.ElevatedButton("Підтвердити", width=300, bgcolor="#FFDDAF", color=ft.colors.BLACK, on_click=verify_otp_click, visible=False)

    def cancel_click(e):
        # Повертаємо форму реєстрації
        register_form.visible = True
        register_btn.visible = True
        login_link.visible = True
        register_btn.disabled = False
        register_btn.text = "Зареєструватися"
        
        # Ховаємо поля введення коду
        otp_form.visible = False
        verify_btn.visible = False
        cancel_btn.visible = False
        
        page.update()

    cancel_btn = ft.ElevatedButton("Назад", width=300, bgcolor="#FFDDAF", color=ft.colors.BLACK, on_click=cancel_click, visible=False)

    def register_click(e):
        name_field.error_text = None
        email_field.error_text = None
        pass_field.error_text = None
        pass_confirm_field.error_text = None
        email_pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'

        if not name_field.value:
            name_field.error_text = "Введіть ваше ім'я"
        elif re.search(r"[0-9!@#$%^&*(),.?\":{}|<>]", name_field.value):
            name_field.error_text = "Ім'я не може містити цифри або спецсимволи"
        elif not re.match(email_pattern, email_field.value):
            email_field.error_text = "Некоректний формат email"
        elif len(pass_field.value) < 8:
            pass_field.error_text = "Пароль має містити мінімум 8 символів"
        elif not re.search(r"[!@#$%^&*(),.?\":{}|<>]", pass_field.value):
            pass_field.error_text = "Додайте хоча б один спецсимвол (!@#$% та ін.)"
        elif pass_field.value != pass_confirm_field.value:
            pass_confirm_field.error_text = "Паролі не співпадають"
        elif check_email_exists(email_field.value):
            email_field.error_text = "Користувач з таким email вже існує."
        else:
            # Блокуємо кнопку, щоб не натиснули двічі
            register_btn.disabled = True
            register_btn.text = "Відправка листа..."
            page.update()
            
            # Генеруємо код і надсилаємо лист
            generated_code = generate_otp()
            current_otp[0] = generated_code
            is_sent = send_otp_email(email_field.value, generated_code)
            
            if is_sent:
                # Перемикаємо інтерфейс на перевірку коду
                register_form.visible = False
                register_btn.visible = False
                login_link.visible = False
                otp_form.visible = True
                verify_btn.visible = True
                cancel_btn.visible = True
            else:
                email_field.error_text = "Помилка відправки. Перевірте email або налаштування .env"
                register_btn.disabled = False
                register_btn.text = "Зареєструватися"
                
        page.update()

    register_btn = ft.ElevatedButton("Зареєструватися", width=300, bgcolor="#FFDDAF", color=ft.colors.BLACK, on_click=register_click)
    login_link = ft.TextButton("Маєте акаунт? Увійти", on_click=lambda e: page.go("/login"))

    return ft.View(
        route="/register",
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=20,
        controls=[
            ft.Icon(name=ft.icons.FLIGHT_TAKEOFF, size=80, color="#FFDDAF"),
            ft.Text("EasyTraveling", size=40, color="#FFDDAF", weight=ft.FontWeight.BOLD),
            ft.Text("Створіть новий акаунт", size=16, color=ft.colors.GREY_400),
            register_form,
            otp_form,
            register_btn,
            verify_btn,
            cancel_btn,
            login_link
            
        ]
    )