import os
import sqlite3
import flet as ft
from database import update_user_name


def create_profile_controller(page: ft.Page, user_id):
    """Ініціалізує діалоги перегляду та редагування профілю і повертає функцію відкриття."""

    def ensure_avatar_column():
        try:
            conn = sqlite3.connect("travel.db")
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(users)")
            columns = [col[1] for col in cursor.fetchall()]
            if "avatar_path" not in columns:
                cursor.execute("ALTER TABLE users ADD COLUMN avatar_path TEXT")
                conn.commit()
            conn.close()
        except Exception as ex:
            print(f"Помилка перевірки колонки avatar_path: {ex}")

    def save_user_avatar(uid, path):
        ensure_avatar_column()
        try:
            conn = sqlite3.connect("travel.db")
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET avatar_path = ? WHERE id = ?", (path, uid))
            conn.commit()
            conn.close()
        except Exception as ex:
            print(f"Помилка збереження аватарки: {ex}")

    def open_dlg(dlg):
        if hasattr(page, "open"):
            page.open(dlg)
        else:
            page.dialog = dlg
            dlg.open = True
            page.update()

    def close_dlg(dlg):
        if hasattr(page, "close"):
            page.close(dlg)
        else:
            dlg.open = False
            page.update()

    def close_profile(e):
        close_dlg(profile_dialog)

    profile_name = ft.Text("Завантаження...", size=20, weight=ft.FontWeight.W_500)
    profile_email = ft.Text("...", color=ft.colors.GREY_400)
    selected_avatar_path = {"path": None}

    main_avatar = ft.Container(
        width=80,
        height=80,
        border_radius=40,
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
        alignment=ft.alignment.center,
        content=ft.Icon(ft.icons.ACCOUNT_CIRCLE, size=80, color=ft.colors.BLUE_700)
    )

    def update_main_avatar():
        path = selected_avatar_path["path"]
        if path and os.path.exists(path):
            main_avatar.content = ft.Image(
                src=path,
                width=80,
                height=80,
                fit=ft.ImageFit.COVER
            )
        else:
            selected_avatar_path["path"] = None
            main_avatar.content = ft.Icon(ft.icons.ACCOUNT_CIRCLE, size=80, color=ft.colors.BLUE_700)

    avatar_picker = ft.FilePicker()
    page.overlay.append(avatar_picker)

    def edit_profile_click(e):
        close_dlg(profile_dialog)

        current_name = profile_name.value if profile_name.value else ""
        current_email = profile_email.value if profile_email.value else ""

        name_input = ft.TextField(label="Ім'я", value=current_name, width=250)
        email_input = ft.TextField(label="Email", value=current_email, width=250, disabled=True)

        temp_avatar = {"path": selected_avatar_path["path"]}

        avatar_preview = ft.Container(
            width=60,
            height=60,
            border_radius=30,
            bgcolor=ft.colors.BLUE_GREY_100,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            alignment=ft.alignment.center,
            content=ft.Image(
                src=temp_avatar["path"],
                width=60,
                height=60,
                fit=ft.ImageFit.COVER
            ) if temp_avatar["path"] else ft.Icon(ft.icons.PERSON, size=32, color=ft.colors.BLUE_700)
        )

        def remove_avatar_click(ev):
            close_dlg(edit_dialog)

            def cancel_delete_photo(e):
                close_dlg(confirm_photo_dlg)
                open_dlg(edit_dialog)

            def confirm_delete_photo(e):
                temp_avatar["path"] = None
                avatar_preview.content = ft.Icon(ft.icons.PERSON, size=32, color=ft.colors.BLUE_700)
                remove_avatar_btn.visible = False
                close_dlg(confirm_photo_dlg)
                open_dlg(edit_dialog)

            confirm_photo_dlg = ft.AlertDialog(
                modal=True,
                title=ft.Text("Видалення фото"),
                content=ft.Text("Ви точно хочете видалити фото профілю?"),
                actions=[
                    ft.TextButton("Скасувати", on_click=cancel_delete_photo),
                    ft.TextButton(
                        "Видалити",
                        on_click=confirm_delete_photo,
                        style=ft.ButtonStyle(color=ft.colors.RED)
                    ),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )

            open_dlg(confirm_photo_dlg)

        remove_avatar_btn = ft.IconButton(
            icon=ft.icons.DELETE_OUTLINE,
            icon_color=ft.colors.RED_400,
            tooltip="Видалити фото",
            visible=bool(temp_avatar["path"]),
            on_click=remove_avatar_click
        )

        def on_avatar_change(ev: ft.FilePickerResultEvent):
            if ev.files and len(ev.files) > 0:
                file_path = ev.files[0].path
                if file_path:
                    temp_avatar["path"] = file_path
                    avatar_preview.content = ft.Image(
                        src=file_path,
                        width=60,
                        height=60,
                        fit=ft.ImageFit.COVER
                    )
                    remove_avatar_btn.visible = True
                    page.update()

        avatar_picker.on_result = on_avatar_change

        def save_click(e):
            new_name = name_input.value.strip()
            if new_name:
                update_user_name(user_id, new_name)
                profile_name.value = new_name

            selected_avatar_path["path"] = temp_avatar["path"]
            save_user_avatar(user_id, temp_avatar["path"])
            update_main_avatar()

            close_dlg(edit_dialog)
            open_dlg(profile_dialog)

        def close_edit(e):
            close_dlg(edit_dialog)
            open_dlg(profile_dialog)

        edit_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Редагувати профіль", text_align=ft.TextAlign.CENTER),
            content=ft.Column([
                ft.Row([
                    avatar_preview,
                    ft.TextButton(
                        "Змінити фото",
                        icon=ft.icons.UPLOAD,
                        on_click=lambda _: avatar_picker.pick_files(
                            allow_multiple=False,
                            file_type=ft.FilePickerFileType.IMAGE
                        )
                    ),
                    remove_avatar_btn
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=5),
                ft.Divider(height=10, color="transparent"),
                name_input,
                email_input
            ], tight=True, alignment=ft.MainAxisAlignment.CENTER),
            actions=[
                ft.TextButton("Скасувати", on_click=close_edit),
                ft.ElevatedButton("Зберегти", on_click=save_click, bgcolor=ft.colors.BLUE, color=ft.colors.WHITE)
            ],
            actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        open_dlg(edit_dialog)

    profile_dialog = ft.AlertDialog(
        title=ft.Text("Мій профіль", weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
        content=ft.Container(
            width=300,
            content=ft.Column([
                main_avatar,
                profile_name,
                profile_email,
                ft.Divider(height=20, color="transparent"),
                ft.ElevatedButton("Редагувати дані", icon=ft.icons.EDIT, width=200, on_click=edit_profile_click),
            ], tight=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        ),
        actions=[
            ft.TextButton("Закрити", on_click=close_profile)
        ],
        actions_alignment=ft.MainAxisAlignment.CENTER,
        shape=ft.RoundedRectangleBorder(radius=15)
    )

    def show_profile(e):
        ensure_avatar_column()
        try:
            conn = sqlite3.connect("travel.db")
            cursor = conn.cursor()
            cursor.execute("SELECT name, email, avatar_path FROM users WHERE id = ?", (user_id,))
            user_data = cursor.fetchone()
            conn.close()

            if user_data:
                profile_name.value = user_data[0]
                profile_email.value = user_data[1]
                selected_avatar_path["path"] = user_data[2]
            else:
                profile_name.value = "Невідомий користувач"
                profile_email.value = f"ID: {user_id}"
                selected_avatar_path["path"] = None

        except Exception as ex:
            profile_name.value = "Помилка БД"
            profile_email.value = str(ex)
            selected_avatar_path["path"] = None

        update_main_avatar()
        open_dlg(profile_dialog)

    return show_profile