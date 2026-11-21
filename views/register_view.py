import flet as ft
import re
from database import create_user, verify_user, check_email_exists
from email_service import generate_otp, send_otp_email


def get_register_view(page: ft.Page):
    current_otp = [""]

    def verify_otp_click(e):
        otp_field.error_text = None
        entered_code = (otp_field.value or "").strip()

        if not entered_code:
            otp_field.error_text = "Введіть 6-значний код"
            page.update()
            return

        if entered_code == current_otp[0]:
            clean_name = (name_field.value or "").strip()
            clean_email = (email_field.value or "").strip().lower()
            raw_pass = pass_field.value or ""

            success = create_user(clean_name, clean_email, raw_pass)
            if success:
                user_id = verify_user(clean_email, raw_pass)
                page.client_storage.set("user_id", user_id)
                page.snack_bar = ft.SnackBar(
                    ft.Text("🎉 Акаунт успішно створено! Ласкаво просимо!", color=ft.colors.WHITE),
                    bgcolor=ft.colors.GREEN_700
                )
                page.snack_bar.open = True
                page.go("/planner")
            else:
                otp_field.error_text = "Помилка збереження користувача в БД"
        else:
            otp_field.error_text = "Неправильний код. Спробуйте ще раз."

        page.update()

    def cancel_click(e):
        register_form.visible = True
        register_btn.visible = True
        login_row.visible = True
        register_btn.disabled = False
        register_btn.text = "Зареєструватися"

        otp_form.visible = False
        verify_btn.visible = False
        cancel_btn.visible = False
        otp_field.value = ""
        otp_field.error_text = None

        page.update()

    def register_click(e):
        name_field.error_text = None
        email_field.error_text = None
        pass_field.error_text = None
        pass_confirm_field.error_text = None

        name_val = (name_field.value or "").strip()
        email_val = (email_field.value or "").strip()
        pass_val = pass_field.value or ""
        confirm_val = pass_confirm_field.value or ""

        email_pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        has_error = False

        # 1. Перевірка імені
        if not name_val:
            name_field.error_text = "Введіть ваше ім'я"
            has_error = True
        elif len(name_val) < 2:
            name_field.error_text = "Ім'я має містити мінімум 2 літери"
            has_error = True
        elif len(name_val) > 50:
            name_field.error_text = "Ім'я занадто довге"
            has_error = True
        elif not re.match(r"^[a-zA-Zа-яА-ЯіІїЇєЄґҐ'\-\s]+$", name_val):
            name_field.error_text = "Ім'я може містити лише літери, дефіс або апостроф"
            has_error = True

        # 2. Перевірка Email
        if not email_val:
            email_field.error_text = "Введіть email"
            has_error = True
        elif not re.match(email_pattern, email_val):
            email_field.error_text = "Некоректний формат email (напр. user@gmail.com)"
            has_error = True
        elif check_email_exists(email_val.lower()):
            email_field.error_text = "Користувач з таким email вже існує"
            has_error = True

        # 3. Перевірка пароля
        if not pass_val:
            pass_field.error_text = "Введіть пароль"
            has_error = True
        elif len(pass_val) < 8:
            pass_field.error_text = "Мінімум 8 символів"
            has_error = True
        elif not re.search(r"[A-Za-z]", pass_val) or not re.search(r"[0-9]", pass_val):
            pass_field.error_text = "Додайте хоча б одну латинську літеру та цифру"
            has_error = True
        elif not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-]", pass_val):
            pass_field.error_text = "Додайте хоча б один спецсимвол (!@#$% та ін.)"
            has_error = True

        # 4. Перевірка підтвердження пароля
        if not confirm_val:
            pass_confirm_field.error_text = "Підтвердіть пароль"
            has_error = True
        elif pass_val != confirm_val:
            pass_confirm_field.error_text = "Паролі не співпадають"
            has_error = True

        if has_error:
            page.update()
            return

        # Блокуємо кнопку на час відправки листа
        register_btn.disabled = True
        register_btn.text = "Відправка листа..."
        page.update()

        generated_code = generate_otp()
        current_otp[0] = generated_code
        is_sent = send_otp_email(email_val.lower(), generated_code)

        if is_sent:
            subtitle_text.value = f"Підтвердження пошти {email_val.lower()}"
            register_form.visible = False
            register_btn.visible = False
            login_row.visible = False

            otp_form.visible = True
            verify_btn.visible = True
            cancel_btn.visible = True
            otp_field.focus()
        else:
            email_field.error_text = "Помилка відправки. Перевірте email або налаштування .env"
            register_btn.disabled = False
            register_btn.text = "Зареєструватися"

        page.update()

    # Поля вводу
    name_field = ft.TextField(
        label="Ім'я",
        width=320,
        border_radius=12,
        prefix_icon=ft.icons.PERSON_OUTLINE,
        autofocus=True,
        on_submit=lambda e: email_field.focus()
    )
    email_field = ft.TextField(
        label="Email",
        hint_text="name@example.com",
        width=320,
        border_radius=12,
        prefix_icon=ft.icons.EMAIL_OUTLINED,
        on_submit=lambda e: pass_field.focus()
    )
    pass_field = ft.TextField(
        label="Пароль",
        width=320,
        border_radius=12,
        password=True,
        can_reveal_password=True,
        prefix_icon=ft.icons.LOCK_OUTLINE,
        on_submit=lambda e: pass_confirm_field.focus()
    )
    pass_confirm_field = ft.TextField(
        label="Підтвердіть пароль",
        width=320,
        border_radius=12,
        password=True,
        can_reveal_password=True,
        prefix_icon=ft.icons.LOCK_RESET,
        on_submit=register_click
    )

    otp_field = ft.TextField(
        label="6-значний код з пошти",
        width=320,
        border_radius=12,
        max_length=6,
        text_align=ft.TextAlign.CENTER,
        prefix_icon=ft.icons.MARK_EMAIL_READ_OUTLINED,
        on_submit=verify_otp_click
    )

    subtitle_text = ft.Text(
        "Створіть новий акаунт для подорожей",
        size=14,
        color=ft.colors.GREY_400,
        text_align=ft.TextAlign.CENTER
    )

    register_form = ft.Column(
        [name_field, email_field, pass_field, pass_confirm_field],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=12
    )

    otp_form = ft.Column(
        [
            ft.Container(
                width=320,
                padding=12,
                border_radius=10,
                bgcolor=ft.colors.with_opacity(0.12, ft.colors.BLUE),
                content=ft.Text(
                    "Ми відправили 6-значний код на вашу пошту. Перевірте вхідні (та папку Спам).",
                    text_align=ft.TextAlign.CENTER,
                    size=13,
                    color=ft.colors.BLUE_200
                )
            ),
            otp_field,
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=14,
        visible=False
    )

    register_btn = ft.ElevatedButton(
        text="Зареєструватися",
        icon=ft.icons.PERSON_ADD,
        width=320,
        height=46,
        bgcolor=ft.colors.BLUE,
        color=ft.colors.WHITE,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
        on_click=register_click
    )

    verify_btn = ft.ElevatedButton(
        text="Підтвердити код",
        icon=ft.icons.CHECK_CIRCLE_OUTLINE,
        width=320,
        height=46,
        bgcolor=ft.colors.GREEN_700,
        color=ft.colors.WHITE,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
        on_click=verify_otp_click,
        visible=False
    )

    cancel_btn = ft.OutlinedButton(
        text="Назад до даних",
        icon=ft.icons.ARROW_BACK,
        width=320,
        height=42,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
        on_click=cancel_click,
        visible=False
    )

    login_row = ft.Row(
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=4,
        controls=[
            ft.Text("Вже маєте акаунт?", size=13, color=ft.colors.GREY_400),
            ft.TextButton(
                "Увійти",
                style=ft.ButtonStyle(color=ft.colors.BLUE_300),
                on_click=lambda e: page.go("/login")
            )
        ]
    )

    register_card = ft.Container(
        width=400,
        padding=32,
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
            spacing=14,
            controls=[
                ft.Container(
                    padding=14,
                    border_radius=50,
                    bgcolor=ft.colors.with_opacity(0.15, ft.colors.BLUE),
                    content=ft.Icon(ft.icons.EXPLORE, size=44, color=ft.colors.BLUE_400)
                ),
                ft.Text("EasyTraveling", size=28, weight=ft.FontWeight.W_800),
                subtitle_text,
                ft.Divider(height=4, color="transparent"),
                register_form,
                otp_form,
                register_btn,
                verify_btn,
                cancel_btn,
                login_row
            ]
        )
    )

    return ft.View(
        route="/register",
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        scroll=ft.ScrollMode.AUTO,
        controls=[register_card]
    )