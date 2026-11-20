import flet as ft
import requests
import sqlite3
import re
import urllib.parse
import webbrowser
from database import update_user_name
from api_service import search_flights, check_city_exists
from trip_manager import generate_trip_plan


def get_city_weather(city_name):
    """Отримує поточну температуру міста через безкоштовний Open-Meteo API (без ключів)."""
    try:
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={urllib.parse.quote(city_name)}&count=1&language=uk&format=json"
        geo_res = requests.get(geo_url, timeout=4).json()
        if not geo_res.get("results"):
            return None
        lat = geo_res["results"][0]["latitude"]
        lon = geo_res["results"][0]["longitude"]

        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,weather_code"
        w_res = requests.get(weather_url, timeout=4).json()
        temp = w_res.get("current", {}).get("temperature_2m")
        code = w_res.get("current", {}).get("weather_code", 0)

        if code == 0:
            desc = "☀️ Ясно"
        elif code in [1, 2, 3]:
            desc = "⛅ Хмарно"
        elif code in [45, 48]:
            desc = "🌫 Туман"
        elif code in [51, 53, 55, 61, 63, 65, 80, 81, 82]:
            desc = "🌧 Дощ"
        elif code in [71, 73, 75, 77, 85, 86]:
            desc = "❄️ Сніг"
        else:
            desc = "🌤 Мінливо"

        return f"{desc}, {round(temp)}°C" if temp is not None else None
    except Exception:
        return None


def calculate_min_budget(cheap_flights):
    """Витягує ціни з рядків найдешевших квитків туди й назад і рахує суму."""
    total = 0
    found = 0
    for item in cheap_flights:
        match = re.search(r'(\d+(?:[.,]\d+)?)\s*€', str(item))
        if match:
            total += float(match.group(1).replace(",", "."))
            found += 1
    if found > 0:
        return f"{int(total) if total.is_integer() else round(total, 2)}€"
    return None


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

    # --- Поля вводу міст + кнопка обміну місцями ---
    origin_field = ft.TextField(label="Звідки", width=195, border_radius=10, prefix_icon=ft.icons.FLIGHT_TAKEOFF)
    destination_field = ft.TextField(label="Куди", width=195, border_radius=10, prefix_icon=ft.icons.FLIGHT_LAND)

    def swap_cities(e):
        origin_field.value, destination_field.value = destination_field.value, origin_field.value
        page.update()

    swap_btn = ft.IconButton(
        icon=ft.icons.SWAP_HORIZ,
        tooltip="Поміняти міста місцями",
        icon_color=ft.colors.BLUE_400,
        on_click=swap_cities
    )

    start_btn = ft.ElevatedButton("Дата вильоту", icon=ft.icons.CALENDAR_MONTH, width=195, on_click=lambda e: start_picker.pick_date())
    end_btn = ft.ElevatedButton("Дата повернення", icon=ft.icons.CALENDAR_MONTH, width=195, on_click=lambda e: end_picker.pick_date())

    results_container = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)

    # --- Картки популярних напрямків (поки не згенеровано тур) ---
    def select_preset(orig, dest):
        origin_field.value = orig
        destination_field.value = dest
        page.snack_bar = ft.SnackBar(
            ft.Text(f"Обрано маршрут {orig} ➔ {dest}. Тепер оберіть дати!", color=ft.colors.WHITE),
            bgcolor=ft.colors.BLUE_700
        )
        page.snack_bar.open = True
        page.update()

    def create_preset_card(emoji, title, route_text, orig, dest, price_hint):
        return ft.Container(
            width=210,
            padding=15,
            border_radius=14,
            bgcolor=ft.colors.with_opacity(0.06, ft.colors.WHITE),
            border=ft.border.all(1, ft.colors.with_opacity(0.12, ft.colors.WHITE)),
            ink=True,
            on_click=lambda e: select_preset(orig, dest),
            content=ft.Column([
                ft.Row([
                    ft.Text(emoji, size=24),
                    ft.Container(
                        padding=ft.padding.symmetric(horizontal=8, vertical=3),
                        border_radius=8,
                        bgcolor=ft.colors.with_opacity(0.2, ft.colors.GREEN),
                        content=ft.Text(price_hint, size=11, color=ft.colors.GREEN_300, weight=ft.FontWeight.BOLD)
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Text(title, size=16, weight=ft.FontWeight.BOLD),
                ft.Text(route_text, size=12, color=ft.colors.GREY_400),
            ], spacing=6)
        )

    presets_block = ft.Column(
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Text("✨ Популярні напрямки для натхнення", size=15, color=ft.colors.GREY_400, weight=ft.FontWeight.W_500),
            ft.Divider(height=8, color="transparent"),
            ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                wrap=True,
                spacing=15,
                controls=[
                    create_preset_card("🇮🇹", "Вікенд у Римі", "Краків ➔ Рим", "Краків", "Рим", "від 65€"),
                    create_preset_card("🇦🇹", "Кава у Відні", "Варшава ➔ Відень", "Варшава", "Відень", "від 50€"),
                    create_preset_card("🇪🇸", "Сонце Барселони", "Краків ➔ Барселона", "Краків", "Барселона", "від 80€"),
                    create_preset_card("🇫🇷", "Романтика Парижа", "Варшава ➔ Париж", "Варшава", "Париж", "від 75€"),
                ]
            )
        ]
    )
    results_container.controls.append(presets_block)

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
            ft.Row([
                ft.ProgressRing(width=20, height=20, stroke_width=2),
                ft.Text("Шукаємо найкращі авіаквитки та перевіряємо погоду...", color=ft.colors.BLUE_300)
            ], alignment=ft.MainAxisAlignment.CENTER)
        )
        page.update()

        flight_data = search_flights(
            origin=origin_field.value,
            destination=destination_field.value,
            date=f"{start_btn.text} — {end_btn.text}"
        )

        weather_info = get_city_weather(destination_field.value)

        results_container.controls.clear()
        results_container.controls.append(
            ft.Row([
                ft.ProgressRing(width=20, height=20, stroke_width=2, color=ft.colors.ORANGE),
                ft.Text("Квитки знайдено! Groq формує персональний план подорожі...", color=ft.colors.ORANGE_300)
            ], alignment=ft.MainAxisAlignment.CENTER)
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

        if type(ai_plan) is dict:
            flights_data = ai_plan.get("flights", {})
            if isinstance(flights_data, list):
                flights_data = {"cheap": flights_data, "medium": [], "expensive": []}

            cheap_list = flights_data.get("cheap", [])
            min_budget = calculate_min_budget(cheap_list)

            # Верхній банер-зведення: маршрут, погода, мінімальний бюджет
            summary_badges = [
                ft.Text(f"✈️ {origin_field.value} ➔ {destination_field.value}", size=18, weight=ft.FontWeight.BOLD)
            ]
            if weather_info:
                summary_badges.append(
                    ft.Container(
                        padding=ft.padding.symmetric(horizontal=12, vertical=6),
                        border_radius=20,
                        bgcolor=ft.colors.with_opacity(0.15, ft.colors.BLUE),
                        content=ft.Text(f"Погода зараз: {weather_info}", size=13, color=ft.colors.BLUE_200, weight=ft.FontWeight.W_500)
                    )
                )
            if min_budget:
                summary_badges.append(
                    ft.Container(
                        padding=ft.padding.symmetric(horizontal=12, vertical=6),
                        border_radius=20,
                        bgcolor=ft.colors.with_opacity(0.18, ft.colors.GREEN),
                        content=ft.Text(f"💰 Переліт від {min_budget}", size=13, color=ft.colors.GREEN_300, weight=ft.FontWeight.BOLD)
                    )
                )

            summary_bar = ft.Container(
                padding=ft.padding.symmetric(horizontal=18, vertical=12),
                border_radius=12,
                bgcolor=ft.colors.with_opacity(0.05, ft.colors.WHITE),
                border=ft.border.all(1, ft.colors.with_opacity(0.1, ft.colors.WHITE)),
                content=ft.Row(
                    controls=summary_badges,
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    wrap=True
                )
            )

            def create_flight_column(title, flights_list, color):
                return ft.Column(
                    controls=[
                        ft.Text(title, weight=ft.FontWeight.BOLD, color=color, size=15),
                        *[ft.Text(f, size=13) for f in flights_list]
                    ],
                    expand=1
                )

            flights_row = ft.Row(
                controls=[
                    create_flight_column("🟢 Дешеві", cheap_list, ft.colors.GREEN),
                    create_flight_column("🟡 Середні", flights_data.get("medium", []), ft.colors.AMBER),
                    create_flight_column("🔴 Дорогі", flights_data.get("expensive", []), ft.colors.RED),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.START
            )

            # Клікабельні чіпси локацій з відкриттям Google Maps
            def open_map(place_name):
                query = urllib.parse.quote(f"{place_name}, {destination_field.value}")
                url = f"https://www.google.com/maps/search/?api=1&query={query}"
                webbrowser.open(url)

            place_buttons = [
                ft.ElevatedButton(
                    text=place,
                    icon=ft.icons.MAP_OUTLINED,
                    tooltip="Відкрити на Google Картах",
                    style=ft.ButtonStyle(
                        bgcolor=ft.colors.with_opacity(0.12, ft.colors.BLUE),
                        color=ft.colors.BLUE_200,
                    ),
                    on_click=lambda e, p=place: open_map(p)
                )
                for place in ai_plan.get("places", [])
            ]

            results_container.controls.extend([
                summary_bar,
                ft.Divider(height=8, color="transparent"),
                ft.Card(
                    elevation=3,
                    content=ft.Container(
                        padding=18,
                        content=flights_row
                    )
                ),
                ft.Divider(height=10, color="transparent"),
                ft.Text("📍 Обов'язково відвідати (натисніть, щоб відкрити на карті):", weight=ft.FontWeight.W_500, color=ft.colors.GREY_300),
                ft.Row(
                    controls=place_buttons,
                    wrap=True,
                    spacing=10
                ),
                ft.Divider(height=10, color="transparent"),
                ft.Container(
                    bgcolor=ft.colors.AMBER_100,
                    padding=15,
                    border_radius=12,
                    content=ft.Row([
                        ft.Icon(ft.icons.LIGHTBULB, color=ft.colors.AMBER_800),
                        ft.Text(ai_plan.get("tip", ""), color=ft.colors.BLACK87, expand=True, weight=ft.FontWeight.W_500)
                    ])
                )
            ])

            # --- АВТОМАТИЧНЕ ЗБЕРЕЖЕННЯ В БАЗУ ---
            try:
                import json
                conn = sqlite3.connect("travel.db")
                cursor = conn.cursor()
                cursor.execute('''CREATE TABLE IF NOT EXISTS saved_trips (
                                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                                    user_id INTEGER,
                                    origin TEXT,
                                    destination TEXT,
                                    dates TEXT,
                                    plan_data TEXT
                                )''')
                plan_str = json.dumps(ai_plan, ensure_ascii=False)
                cursor.execute('''INSERT INTO saved_trips (user_id, origin, destination, dates, plan_data)
                                  VALUES (?, ?, ?, ?, ?)''',
                               (user_id, origin_field.value, destination_field.value, f"{start_btn.text} — {end_btn.text}", plan_str))
                conn.commit()
                conn.close()

                page.snack_bar = ft.SnackBar(ft.Text("✅ Маршрут успішно збережено в профіль!", color=ft.colors.WHITE), bgcolor=ft.colors.GREEN)
                page.snack_bar.open = True

            except Exception as ex:
                print(f"Помилка збереження в БД: {ex}")

        else:
            results_container.controls.append(ft.Text("Не вдалося згенерувати план.", color=ft.colors.RED))

        btn.disabled = False
        btn.text = "Згенерувати тур"
        btn.update()
        page.update()

    generate_btn = ft.ElevatedButton(
        text="Згенерувати тур",
        icon=ft.icons.AUTO_AWESOME,
        on_click=on_generate_click,
        bgcolor=ft.colors.BLUE,
        color=ft.colors.WHITE,
        height=45,
        width=220
    )

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
                padding=ft.padding.symmetric(horizontal=40, vertical=25),
                content=ft.Column(
                    alignment=ft.MainAxisAlignment.START,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Text("Сплануйте нову подорож", size=28, weight=ft.FontWeight.BOLD),
                        ft.Divider(height=8, color="transparent"),
                        ft.Row([origin_field, swap_btn, destination_field], alignment=ft.MainAxisAlignment.CENTER),
                        ft.Row([start_btn, end_btn], alignment=ft.MainAxisAlignment.CENTER, spacing=15),
                        ft.Divider(height=8, color="transparent"),
                        generate_btn,
                        ft.Divider(height=15),
                        ft.Container(
                            expand=True,
                            content=ft.Column([results_container], scroll=ft.ScrollMode.AUTO)
                        )
                    ]
                )
            )
        ]
    )