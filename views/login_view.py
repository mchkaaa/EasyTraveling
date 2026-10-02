import flet as ft
import re

def get_login_view(page: ft.Page):
    email_field = ft.TextField(label="Email", width=300, prefix_icon=ft.icons.EMAIL)
    pass_field = ft.TextField(label="Пароль", width=300, password=True, can_reveal_password=True, prefix_icon=ft.icons.LOCK)

    def login_click(e):
        email_field.error_text = None
        pass_field.error_text = None
        email_pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'

        if not email_field.value:
            email_field.error_text = "Введіть email"
        elif not re.match(email_pattern, email_field.value):
            email_field.error_text = "Некоректний формат email"
        elif not pass_field.value:
            pass_field.error_text = "Введіть пароль"
        elif len(pass_field.value) < 8:
            pass_field.error_text = "Пароль має містити мінімум 8 символів"
        elif not re.search(r"[!@#$%^&*(),.?\":{}|<>]", pass_field.value):
            pass_field.error_text = "Додайте хоча б один спецсимвол (!@#$% та ін.)"
        else:
            page.go("/planner")

        page.update()

    return ft.View(
        route="/login",
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=20,
        controls=[
            ft.Icon(name=ft.icons.FLIGHT_TAKEOFF, size=80, color="#FFDDAF"),
            ft.Text("EasyTraveling", size=40, color="#FFDDAF", weight=ft.FontWeight.BOLD),
            ft.Text("Сплануйте свою ідеальну поїздку", size=16, color=ft.colors.GREY_400),
            email_field,
            pass_field,
            ft.ElevatedButton("Увійти", width=300, bgcolor="#FFDDAF", color=ft.colors.BLACK, on_click=login_click),
            ft.TextButton("Немає акаунту? Зареєструватися", on_click=lambda e: page.go("/register"))
        ]
    )