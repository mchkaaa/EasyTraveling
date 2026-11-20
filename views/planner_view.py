import flet as ft
import requests
import sqlite3
from database import update_user_name
from api_service import search_flights, check_city_exists
from trip_manager import generate_trip_plan

def get_planner_view(page: ft.Page):
    user_id = page.client_storage.get("user_id")

    # --- Спливаюче вікно для підтвердження виходу ---
    def close_dialog(e):
        confirm_dialog.open = False
        page.update()

    def do_logout(e):
        confirm_dialog.open = False
        page.client_storage.remove("user_id")
        page.go("/login")

    confirm_dialog = ft.AlertDialog(
        title=ft.Text("Підтвердження"),
        content=ft.Text("Ви дійсно хочете вийти з акаунту?"),
        actions=[
            ft.TextButton("Скасувати", on_click=close_dialog),
            ft.TextButton("Вийти", on_click=do_logout, style=ft.ButtonStyle(color=ft.colors.RED)),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    def logout_click(e):
        page.dialog = confirm_dialog
        confirm_dialog.open = True
        page.update()

    # --- Допоміжна функція для збереження аватарки в БД ---
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

    # --- Вікно профілю ---
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
        import os
        path = selected_avatar_path["path"]
        # Перевіряємо, чи існує шлях і сам файл на диску
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

    # 2. Функція вікна редагування
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

        # Функція видалення фото з вікном підтвердження
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

            # Зберігаємо шлях до фото в БД (або None, якщо фото видалили)
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

    # 3. Головне вікно профілю
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
    def go_to_trips(e):
        page.go("/trips")

    # --- Функції та віджети для календаря ---
    def change_start_date(e):
        if start_picker.value:
            start_btn.text = f"З: {start_picker.value.strftime('%d.%m.%Y')}"
            page.update()

    def change_end_date(e):
        if end_picker.value:
            end_btn.text = f"По: {end_picker.value.strftime('%d.%m.%Y')}"
            page.update()

    start_picker = ft.DatePicker(on_change=change_start_date)
    end_picker = ft.DatePicker(on_change=change_end_date)
    
    page.overlay.extend([start_picker, end_picker])

    # --- Прості текстові поля для вводу міст ---
    origin_field = ft.TextField(label="Звідки", width=195)
    destination_field = ft.TextField(label="Куди", width=195)
    
    start_btn = ft.ElevatedButton("Дата вильоту", icon=ft.icons.CALENDAR_MONTH, width=195, on_click=lambda e: start_picker.pick_date())
    end_btn = ft.ElevatedButton("Дата повернення", icon=ft.icons.CALENDAR_MONTH, width=195, on_click=lambda e: end_picker.pick_date())
    
    # Контейнер для результатів (без фіксованої висоти, щоб він розтягувався в межах батьківського)
    results_container = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)

    # --- Логіка генерації туру ---
    def on_generate_click(e):
        btn = e.control
        
        if not origin_field.value or not destination_field.value or start_btn.text == "Дата вильоту" or end_btn.text == "Дата повернення":
            page.snack_bar = ft.SnackBar(ft.Text("Помилка: Заповніть всі поля та оберіть дати!", color=ft.colors.WHITE), bgcolor=ft.colors.RED)
            page.snack_bar.open = True
            page.update()
            return

        if len(origin_field.value) < 2 or len(destination_field.value) < 2:
            page.snack_bar = ft.SnackBar(ft.Text("Помилка: Назва міста має містити хоча б 2 літери!", color=ft.colors.WHITE), bgcolor=ft.colors.RED)
            page.snack_bar.open = True
            page.update()
            return

        btn.disabled = True
        btn.text = "Перевірка міст..."
        btn.update()

        real_origin = check_city_exists(origin_field.value)
        if not real_origin:
            page.snack_bar = ft.SnackBar(ft.Text(f"Місто '{origin_field.value}' не знайдено!", color=ft.colors.WHITE), bgcolor=ft.colors.RED)
            page.snack_bar.open = True
            btn.disabled = False
            btn.text = "Згенерувати тур"
            btn.update()
            page.update()
            return
        else:
            origin_field.value = real_origin 
            
        real_dest = check_city_exists(destination_field.value)
        if not real_dest:
            page.snack_bar = ft.SnackBar(ft.Text(f"Місто '{destination_field.value}' не знайдено!", color=ft.colors.WHITE), bgcolor=ft.colors.RED)
            page.snack_bar.open = True
            btn.disabled = False
            btn.text = "Згенерувати тур"
            btn.update()
            page.update()
            return
        else:
            destination_field.value = real_dest

        page.update()

        results_container.controls.clear()
        results_container.controls.append(
            ft.Text("⏳ Шукаємо найкращі авіаквитки...", color=ft.colors.BLUE)
        )
        page.update()

        # 5. Отримуємо дані про квитки
        flight_data = search_flights(
            origin=origin_field.value,
            destination=destination_field.value,
            date=f"{start_btn.text} — {end_btn.text}"
        )

        # --- ДОДАЙ ЦЕЙ БЛОК ДЛЯ ПЕРЕВІРКИ ---
        print("========== ДАНІ ВІД API ==========")
        print(flight_data)
        print("==================================")

        results_container.controls.clear()
        results_container.controls.append(
            ft.Text("🧠 Квитки знайдено! Groq формує план подорожі...", color=ft.colors.ORANGE)
        )
        btn.text = "AI працює..."
        btn.update()
        page.update()

        ai_plan = generate_trip_plan(
            origin=origin_field.value,
            destination=destination_field.value,
            date=f"{start_btn.text} — {end_btn.text}",
            flight_data=flight_data
        )

        results_container.controls.clear()

        # 8. Виводимо результат у колонки
        if type(ai_plan) is dict:
            flights_data = ai_plan.get("flights", {})
            
            # Підстраховка: якщо ШІ все ще повертає список замість словника
            if isinstance(flights_data, list):
                flights_data = {"cheap": flights_data, "medium": [], "expensive": []}

            def create_flight_column(title, flights_list, color):
                return ft.Column(
                    controls=[
                        ft.Text(title, weight=ft.FontWeight.BOLD, color=color),
                        *[ft.Text(f, size=13) for f in flights_list]
                    ],
                    expand=1 # Щоб колонки рівномірно ділили ширину
                )

            flights_row = ft.Row(
                controls=[
                    create_flight_column("🟢 Дешеві", flights_data.get("cheap", []), ft.colors.GREEN),
                    create_flight_column("🟡 Середні", flights_data.get("medium", []), ft.colors.AMBER),
                    create_flight_column("🔴 Дорогі", flights_data.get("expensive", []), ft.colors.RED),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.START
            )

            results_container.controls.extend([
                ft.Card(
                    content=ft.Container(
                        padding=15,
                        content=flights_row
                    )
                ),
                ft.Divider(height=10, color="transparent"),
                ft.Text("📍 Обов'язково відвідати:", weight=ft.FontWeight.W_500, color=ft.colors.GREY_700),
                ft.Row(
                    controls=[
                        ft.ElevatedButton(text=place, icon=ft.icons.LOCATION_ON, disabled=True) 
                        for place in ai_plan.get("places", [])
                    ],
                    wrap=True 
                ),
                ft.Divider(height=10, color="transparent"),
                ft.Container(
                    bgcolor=ft.colors.AMBER_100,
                    padding=15,
                    border_radius=10,
                    content=ft.Row([
                        ft.Icon(ft.icons.LIGHTBULB, color=ft.colors.AMBER_700),
                        ft.Text(ai_plan.get("tip", ""), color=ft.colors.BLACK87, expand=True) # expand=True захищає текст від обрізання
                    ])
                )
            ])

            # --- НОВИЙ КОД: АВТОМАТИЧНЕ ЗБЕРЕЖЕННЯ В БАЗУ ---
            try:
                import json
                conn = sqlite3.connect("travel.db")
                cursor = conn.cursor()
                
                # Створюємо НОВУ таблицю з іншою назвою (saved_trips)
                cursor.execute('''CREATE TABLE IF NOT EXISTS saved_trips (
                                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                                    user_id INTEGER,
                                    origin TEXT,
                                    destination TEXT,
                                    dates TEXT,
                                    plan_data TEXT
                                )''')
                
                # Зберігаємо дані маршруту 
                plan_str = json.dumps(ai_plan, ensure_ascii=False)
                cursor.execute('''INSERT INTO saved_trips (user_id, origin, destination, dates, plan_data)
                                  VALUES (?, ?, ?, ?, ?)''', 
                               (user_id, origin_field.value, destination_field.value, f"{start_btn.text} — {end_btn.text}", plan_str))
                
                conn.commit()
                conn.close()

                # Зелене повідомлення про успішне збереження
                page.snack_bar = ft.SnackBar(ft.Text("✅ Маршрут успішно збережено в профіль!", color=ft.colors.WHITE), bgcolor=ft.colors.GREEN)
                page.snack_bar.open = True
                
            except Exception as ex:
                print(f"Помилка збереження в БД: {ex}")
            # ------------------------------------------------

        else:
            results_container.controls.append(ft.Text("Не вдалося згенерувати план.", color=ft.colors.RED))
            
        btn.disabled = False
        btn.text = "Згенерувати тур"
        btn.update()
        page.update()

    generate_btn = ft.ElevatedButton(text="Згенерувати тур", on_click=on_generate_click, bgcolor=ft.colors.BLUE, color=ft.colors.WHITE)

    return ft.View(
        "/planner",
        controls=[
            ft.AppBar(
                leading=ft.Icon(ft.icons.EXPLORE, color=ft.colors.WHITE, size=32),
                leading_width=50,
                title=ft.Text(
                    "EasyTraveling", 
                    size=22, 
                    weight=ft.FontWeight.W_800, 
                    color=ft.colors.WHITE
                ),
                center_title=False,
                bgcolor=ft.colors.BLUE_900,
                elevation=5, 
                shadow_color=ft.colors.BLACK26,
                actions=[
                    ft.Container(
                        margin=ft.margin.only(right=15),
                        content=ft.PopupMenuButton(
                            icon=ft.icons.ACCOUNT_CIRCLE,
                            icon_size=32,
                            icon_color=ft.colors.WHITE,
                            tooltip="Меню користувача",
                            items=[
                                ft.PopupMenuItem(text="Мій профіль", icon=ft.icons.PERSON, on_click=show_profile),
                                ft.PopupMenuItem(
                                    text="Мої подорожі", 
                                    icon=ft.icons.BOOKMARKS, 
                                    on_click=go_to_trips
                                ),
                                ft.PopupMenuItem(), 
                                ft.PopupMenuItem(
                                    text="Вийти", 
                                    icon=ft.icons.LOGOUT, 
                                    on_click=logout_click
                                ),
                            ]
                        )
                    )
                ]
            ),
            ft.Container(
                expand=True,
                padding=40,
                content=ft.Column(
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Text("Сплануйте нову подорож", size=28, weight=ft.FontWeight.BOLD),
                        ft.Divider(height=10, color="transparent"),
                        ft.Row([origin_field, destination_field], alignment=ft.MainAxisAlignment.CENTER),
                        start_btn,
                        end_btn,
                        ft.Divider(height=10, color="transparent"),
                        generate_btn,
                        ft.Divider(height=20),
                        ft.Container(
                            expand=True,
                            content=ft.Column([results_container], scroll=ft.ScrollMode.AUTO)
                        )
                    ]
                )
            )
        ]
    )