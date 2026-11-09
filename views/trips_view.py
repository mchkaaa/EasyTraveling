import flet as ft
import sqlite3
import json

def get_trips_view(page: ft.Page):
    user_id = page.client_storage.get("user_id")
    
    # Головний контейнер для списку зі скролом
    trips_list = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True, spacing=15)

    def load_trips():
        trips_list.controls.clear()
        try:
            conn = sqlite3.connect("travel.db")
            cursor = conn.cursor()
            # Читаємо з нашої НОВОЇ таблиці
            cursor.execute("SELECT origin, destination, dates, plan_data FROM saved_trips WHERE user_id = ? ORDER BY id DESC", (user_id,))
            rows = cursor.fetchall()
            conn.close()

            if not rows:
                trips_list.controls.append(
                    ft.Container(
                        content=ft.Text("У вас поки немає збережених маршрутів.", size=18, color=ft.colors.GREY),
                        alignment=ft.alignment.center,
                        padding=50
                    )
                )
                return

            for row in rows:
                origin, dest, dates, plan_data_str = row
                
                try:
                    plan_data = json.loads(plan_data_str)
                except:
                    continue # Пропускаємо пошкоджені записи
                
                # Витягуємо рейси
                flights_data = plan_data.get("flights", {})
                if isinstance(flights_data, list):
                    flights_data = {"cheap": flights_data, "medium": [], "expensive": []}

                def create_flight_col(title, f_list, color):
                    return ft.Column(
                        controls=[ft.Text(title, weight=ft.FontWeight.BOLD, color=color)] + [ft.Text(f, size=13) for f in f_list],
                        expand=1
                    )

                flights_row = ft.Row([
                    create_flight_col("🟢 Дешеві", flights_data.get("cheap", []), ft.colors.GREEN),
                    create_flight_col("🟡 Середні", flights_data.get("medium", []), ft.colors.AMBER),
                    create_flight_col("🔴 Дорогі", flights_data.get("expensive", []), ft.colors.RED),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.START)

                places_row = ft.Row(
                    controls=[ft.ElevatedButton(text=p, icon=ft.icons.LOCATION_ON, disabled=True) for p in plan_data.get("places", [])],
                    wrap=True
                )

                tip_container = ft.Container(
                    bgcolor=ft.colors.AMBER_100, padding=15, border_radius=10,
                    content=ft.Row([ft.Icon(ft.icons.LIGHTBULB, color=ft.colors.AMBER_700), ft.Text(plan_data.get("tip", ""), color=ft.colors.BLACK87, expand=True)])
                )

                # Створюємо картку, що розгортається вниз (щоб екран не був надто довгим)
                trip_card = ft.ExpansionTile(
                    title=ft.Text(f"{origin} ➔ {dest}", weight=ft.FontWeight.BOLD, size=18),
                    subtitle=ft.Text(f"Дати: {dates}", color=ft.colors.BLUE_700),
                    leading=ft.Icon(ft.icons.MAP, color=ft.colors.BLUE),
                    controls_padding=20,
                    controls=[
                        flights_row,
                        ft.Divider(height=20, color="transparent"),
                        ft.Text("📍 Локації:", weight=ft.FontWeight.W_500),
                        places_row,
                        ft.Divider(height=10, color="transparent"),
                        tip_container
                    ]
                )
                
                trips_list.controls.append(ft.Card(content=trip_card, elevation=3))

        except Exception as e:
            trips_list.controls.append(ft.Text(f"Помилка БД: {e}", color=ft.colors.RED))

    # Викликаємо завантаження при відкритті сторінки
    load_trips()

    return ft.View(
        "/trips",
        controls=[
            ft.AppBar(
                leading=ft.IconButton(ft.icons.ARROW_BACK, icon_color=ft.colors.WHITE, on_click=lambda e: page.go("/planner")),
                title=ft.Text("Мої збережені подорожі", color=ft.colors.WHITE, weight=ft.FontWeight.BOLD),
                bgcolor=ft.colors.BLUE_900
            ),
            ft.Container(expand=True, padding=20, content=trips_list)
        ]
    )