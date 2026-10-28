import flet as ft
import requests
from api_service import search_flights
from trip_manager import generate_trip_plan
from api_service import search_flights, check_city_exists

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
    
    results_container = ft.Column()

    # --- Логіка генерації туру ---
    def on_generate_click(e):
        btn = e.control
        
        # 1. Базова перевірка на порожні поля
        if not origin_field.value or not destination_field.value or start_btn.text == "Дата вильоту" or end_btn.text == "Дата повернення":
            page.snack_bar = ft.SnackBar(ft.Text("Помилка: Заповніть всі поля та оберіть дати!", color=ft.colors.WHITE), bgcolor=ft.colors.RED)
            page.snack_bar.open = True
            page.update()
            return

        # 2. Перевірка на надто короткі назви
        if len(origin_field.value) < 2 or len(destination_field.value) < 2:
            page.snack_bar = ft.SnackBar(ft.Text("Помилка: Назва міста має містити хоча б 2 літери!", color=ft.colors.WHITE), bgcolor=ft.colors.RED)
            page.snack_bar.open = True
            page.update()
            return

        # Блокуємо кнопку на час перевірки
        btn.disabled = True
        btn.text = "Перевірка міст..."
        btn.update()

        # 3. Контрольна перевірка API та АВТОВИПРАВЛЕННЯ
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

        # Оновлюємо поля в інтерфейсі (якщо були виправлення)
        page.update()

        # 4. Показуємо індикатор завантаження квитків
        results_container.controls.clear()
        results_container.controls.append(
            ft.Text("⏳ Шукаємо найкращі авіаквитки через RapidAPI...", color=ft.colors.BLUE)
        )
        page.update()

        # 5. Отримуємо дані про квитки
        flight_data = search_flights(
            origin=origin_field.value,
            destination=destination_field.value,
            date=f"{start_btn.text} — {end_btn.text}"
        )

        # 6. Оновлюємо статус для Gemini
        results_container.controls.clear()
        results_container.controls.append(
            ft.Text("🧠 Квитки знайдено! Gemini формує план подорожі...", color=ft.colors.ORANGE)
        )
        btn.text = "Gemini працює..."
        btn.update()
        page.update()

        # 7. Запит до ШІ
        ai_plan = generate_trip_plan(
            origin=origin_field.value,
            destination=destination_field.value,
            date=f"{start_btn.text} — {end_btn.text}",
            flight_data=flight_data
        )

        results_container.controls.clear()

        # 8. Виводимо результат
        if type(ai_plan) is dict:
            flights_list = ai_plan.get("flights", ["Немає даних про рейси"])
            
            flight_rows = [
                ft.Container(
                    padding=10,
                    content=ft.Row([
                        ft.Icon(ft.icons.FLIGHT_TAKEOFF, color=ft.colors.BLUE),
                        ft.Text(flight_text, weight=ft.FontWeight.BOLD)
                    ])
                )
                for flight_text in flights_list
            ]

            results_container.controls.extend([
                ft.Card(content=ft.Column(flight_rows, spacing=0)),
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
                        ft.Text(ai_plan.get("tip", ""), color=ft.colors.BLACK87)
                    ])
                )
            ])
        else:
            results_container.controls.append(ft.Text("Не вдалося згенерувати план.", color=ft.colors.RED))
            
        # Повертаємо кнопку в початковий стан
        btn.disabled = False
        btn.text = "Згенерувати тур"
        btn.update()
        page.update()

    generate_btn = ft.ElevatedButton(text="Згенерувати тур", on_click=on_generate_click, bgcolor=ft.colors.BLUE, color=ft.colors.WHITE)

    return ft.View(
        "/planner",
        controls=[
            ft.AppBar(
                title=ft.Text("EasyTraveling - Планувальник"), 
                bgcolor=ft.colors.SURFACE_VARIANT,
                actions=[
                    ft.PopupMenuButton(
                        icon=ft.icons.ACCOUNT_CIRCLE,
                        items=[
                            ft.PopupMenuItem(text="Мій профіль", icon=ft.icons.PERSON),
                            ft.PopupMenuItem(text="Вийти", icon=ft.icons.LOGOUT, on_click=logout_click),
                        ]
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
                        ft.Column([results_container], scroll=ft.ScrollMode.AUTO, height=350)
                    ]
                )
            )
        ]
    )