import flet as ft
import re
from database import verify_user


def get_login_view(page: ft.Page):
    def login_click(e):
        email_field.error_text = None
        pass_field.error_text = None

        email_val = (email_field.value or "").strip()
        pass_val = pass_field.value or ""
        email_pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'

        has_error = False

        # 1. Перевірка Email (незалежно від пароля, щоб підсвітити обидва поля за потреби)
        if not email_val:
            email_field.error_text = "Введіть email"
            has_error = True
        elif len(email_val) > 100:
            email_field.error_text = "Email занадто довгий"
            has_error = True
        elif not re.match(email_pattern, email_val):
            email_field.error_text = "Некоректний формат email (напр. user@gmail.com)"
            has_error = True

        # 2. Перевірка пароля
        if not pass_val:
            pass_field.error_text = "Введіть пароль"
            has_error = True
        elif len(pass_val) < 8:
            pass_field.error_text = "Пароль має містити мінімум 8 символів"
            has_error = True

        if has_error:
            page.update()
            return

        # 3. Перевірка в базі даних
        user_id = verify_user(email_val.lower(), pass_val)

        if user_id:
            page.client_storage.set("user_id", user_id)
            page.snack_bar = ft.SnackBar(
                ft.Text("👋 З поверненням у EasyTraveling!", color=ft.colors.WHITE),
                bgcolor=ft.colors.GREEN_700
            )
            page.snack_bar.open = True
            page.go("/planner")
        else:
            pass_field.error_text = "Неправильний email або пароль"
            page.update()

    email_field = ft.TextField(
        label="Email",
        hint_text="name@example.com",
        width=320,
        border_radius=12,
        prefix_icon=ft.icons.EMAIL_OUTLINED,
        autofocus=True,
        on_submit=lambda e: pass_field.focus()
    )

    pass_field = ft.TextField(
        label="Пароль",
        width=320,
        border_radius=12,
        password=True,
        can_reveal_password=True,
        prefix_icon=ft.icons.LOCK_OUTLINE,
        on_submit=login_click  # Вхід по натисканню Enter
    )

    login_card = ft.Container(
        width=400,
        padding=35,
        border_radius=20,
        bgcolor=ft.colors.with_opacity(0.05, ft.colors.WHITE),
        border=ft.border.all(1, ft.colors.with_opacity(0.12, ft.colors.WHITE)),
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=20,
            color=ft.colors.with_opacity(0.25, ft.colors.BLACK),
            offset=ft.Offset(0, 8)
        ),
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=16,
            controls=[
                ft.Container(
                    padding=14,
                    border_radius=50,
                    bgcolor=ft.colors.with_opacity(0.15, ft.colors.BLUE),
                    content=ft.Icon(ft.icons.EXPLORE, size=48, color=ft.colors.BLUE_400)
                ),
                ft.Text("EasyTraveling", size=28, weight=ft.FontWeight.W_800),
                ft.Text(
                    "Увійдіть, щоб планувати свої подорожі",
                    size=14,
                    color=ft.colors.GREY_400,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Divider(height=6, color="transparent"),
                email_field,
                pass_field,
                ft.Divider(height=4, color="transparent"),
                ft.ElevatedButton(
                    text="Увійти",
                    icon=ft.icons.LOGIN,
                    width=320,
                    height=46,
                    bgcolor=ft.colors.BLUE,
                    color=ft.colors.WHITE,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=12)
                    ),
                    on_click=login_click
                ),
                ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=4,
                    controls=[
                        ft.Text("Немає акаунту?", size=13, color=ft.colors.GREY_400),
                        ft.TextButton(
                            "Зареєструватися",
                            style=ft.ButtonStyle(color=ft.colors.BLUE_300),
                            on_click=lambda e: page.go("/register")
                        )
                    ]
                )
            ]
        )
    )

    return ft.View(
        route="/login",
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[login_card]
    )