import flet as ft
import re
from database import create_user

def get_register_view(page: ft.Page):
    name_field = ft.TextField(label="Ім'я", width=300, prefix_icon=ft.icons.PERSON)
    email_field = ft.TextField(label="Email", width=300, prefix_icon=ft.icons.EMAIL)
    pass_field = ft.TextField(label="Пароль", width=300, password=True, can_reveal_password=True, prefix_icon=ft.icons.LOCK)
    pass_confirm_field = ft.TextField(label="Підтвердіть пароль", width=300, password=True, can_reveal_password=True, prefix_icon=ft.icons.LOCK_RESET)

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
        else:
                # Намагаємося зберегти юзера в базу
                success = create_user(name_field.value, email_field.value, pass_field.value)
                
                if success:
                    page.go("/planner")  # Якщо збереглось успішно - пускаємо далі
                else:
                    email_field.error_text = "Користувач з таким email вже існує!"

        page.update()

    return ft.View(
        route="/register",
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=20,
        controls=[
            ft.Icon(name=ft.icons.FLIGHT_TAKEOFF, size=80, color="#FFDDAF"),
            ft.Text("EasyTraveling", size=40, color="#FFDDAF", weight=ft.FontWeight.BOLD),
            ft.Text("Створіть новий акаунт", size=16, color=ft.colors.GREY_400),
            name_field,
            email_field,
            pass_field,
            pass_confirm_field,
            ft.ElevatedButton(
                "Зареєструватися", 
                width=300, 
                bgcolor="#FFDDAF", 
                color=ft.colors.BLACK,
                on_click=register_click
            ),
            ft.TextButton("Маєте акаунт? Увійти", on_click=lambda e: page.go("/login"))
        ]
    )