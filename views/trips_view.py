import flet as ft
import sqlite3
import json
import re
import urllib.parse
import webbrowser

try:
    from database import delete_saved_trip
except ImportError:
    def delete_saved_trip(trip_id):
        conn = sqlite3.connect("travel.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM saved_trips WHERE id = ?", (trip_id,))
        conn.commit()
        conn.close()


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


def get_trips_view(page: ft.Page):
    user_id = page.client_storage.get("user_id")
    trips_list = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True, spacing=15)

    def load_trips():
        trips_list.controls.clear()
        try:
            conn = sqlite3.connect("travel.db")
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, origin, destination, dates, plan_data FROM saved_trips WHERE user_id = ? ORDER BY id DESC",
                (user_id,)
            )
            rows = cursor.fetchall()
            conn.close()

            if not rows:
                trips_list.controls.append(
                    ft.Container(
                        alignment=ft.alignment.center,
                        padding=60,
                        content=ft.Column(
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=15,
                            controls=[
                                ft.Icon(ft.icons.LUGGAGE_OUTLINED, size=72, color=ft.colors.BLUE_GREY_400),
                                ft.Text("У вас поки немає збережених маршрутів", size=20, weight=ft.FontWeight.BOLD, color=ft.colors.GREY_300),
                                ft.Text("Згенеруйте свій перший тур у планувальнику, і він автоматично з'явиться тут.", size=14, color=ft.colors.GREY_500),
                                ft.Divider(height=10, color="transparent"),
                                ft.ElevatedButton(
                                    "Спланувати подорож",
                                    icon=ft.icons.EXPLORE,
                                    bgcolor=ft.colors.BLUE,
                                    color=ft.colors.WHITE,
                                    height=45,
                                    on_click=lambda e: page.go("/planner")
                                )
                            ]
                        )
                    )
                )
                page.update()
                return

            for row in rows:
                trip_id, origin, dest, dates, plan_data_str = row

                try:
                    plan_data = json.loads(plan_data_str)
                except Exception:
                    continue

                flights_data = plan_data.get("flights", {})
                if isinstance(flights_data, list):
                    flights_data = {"cheap": flights_data, "medium": [], "expensive": []}

                cheap_list = flights_data.get("cheap", [])
                min_budget = calculate_min_budget(cheap_list)

                def create_flight_col(title, f_list, color):
                    return ft.Column(
                        controls=[ft.Text(title, weight=ft.FontWeight.BOLD, color=color, size=15)] + [ft.Text(f, size=13) for f in f_list],
                        expand=1
                    )

                flights_row = ft.Row([
                    create_flight_col("🟢 Дешеві", cheap_list, ft.colors.GREEN),
                    create_flight_col("🟡 Середні", flights_data.get("medium", []), ft.colors.AMBER),
                    create_flight_col("🔴 Дорогі", flights_data.get("expensive", []), ft.colors.RED),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.START)

                # Клікабельні чіпси локацій (Google Maps)
                def make_open_map_handler(place_name, city_dest):
                    def open_map(e):
                        query = urllib.parse.quote(f"{place_name}, {city_dest}")
                        webbrowser.open(f"https://www.google.com/maps/search/?api=1&query={query}")
                    return open_map

                places_row = ft.Row(
                    controls=[
                        ft.ElevatedButton(
                            text=p,
                            icon=ft.icons.MAP_OUTLINED,
                            tooltip="Відкрити на Google Картах",
                            style=ft.ButtonStyle(
                                bgcolor=ft.colors.with_opacity(0.12, ft.colors.BLUE),
                                color=ft.colors.BLUE_200,
                            ),
                            on_click=make_open_map_handler(p, dest)
                        )
                        for p in plan_data.get("places", [])
                    ],
                    wrap=True,
                    spacing=10
                )

                tip_container = ft.Container(
                    bgcolor=ft.colors.AMBER_100,
                    padding=15,
                    border_radius=12,
                    content=ft.Row([
                        ft.Icon(ft.icons.LIGHTBULB, color=ft.colors.AMBER_800),
                        ft.Text(plan_data.get("tip", ""), color=ft.colors.BLACK87, expand=True, weight=ft.FontWeight.W_500)
                    ])
                )

                # --- ЛОГІКА ВІКНА ПІДТВЕРДЖЕННЯ ВИДАЛЕННЯ ---
                def make_delete_handler(tid):
                    def delete_click(e):
                        def close_dlg(e):
                            if hasattr(page, "close"):
                                page.close(confirm_dialog)
                            else:
                                confirm_dialog.open = False
                                page.update()

                        def confirm_delete(e):
                            delete_saved_trip(tid)
                            close_dlg(e)
                            page.snack_bar = ft.SnackBar(
                                ft.Text("🗑️ Подорож видалено зі списку.", color=ft.colors.WHITE),
                                bgcolor=ft.colors.BLUE_GREY_800
                            )
                            page.snack_bar.open = True
                            load_trips()

                        confirm_dialog = ft.AlertDialog(
                            modal=True,
                            title=ft.Text("Підтвердження"),
                            content=ft.Text("Ви точно хочете видалити цю подорож?"),
                            actions=[
                                ft.TextButton("Скасувати", on_click=close_dlg),
                                ft.TextButton("Видалити", on_click=confirm_delete, style=ft.ButtonStyle(color=ft.colors.RED)),
                            ],
                            actions_alignment=ft.MainAxisAlignment.END,
                        )

                        if hasattr(page, "open"):
                            page.open(confirm_dialog)
                        else:
                            page.dialog = confirm_dialog
                            confirm_dialog.open = True
                            page.update()

                    return delete_click

                delete_btn = ft.IconButton(
                    icon=ft.icons.DELETE_OUTLINE,
                    icon_color=ft.colors.RED_400,
                    tooltip="Видалити подорож",
                    on_click=make_delete_handler(trip_id)
                )

                # Елементи заголовка: маршрут + бейдж ціни + кошик
                title_controls = [
                    ft.Text(f"{origin} ➔ {dest}", weight=ft.FontWeight.BOLD, size=18),
                ]
                if min_budget:
                    title_controls.append(
                        ft.Container(
                            padding=ft.padding.symmetric(horizontal=10, vertical=4),
                            border_radius=12,
                            bgcolor=ft.colors.with_opacity(0.18, ft.colors.GREEN),
                            content=ft.Text(f"💰 від {min_budget}", size=12, color=ft.colors.GREEN_300, weight=ft.FontWeight.BOLD)
                        )
                    )

                tile_title = ft.Row(
                    controls=[
                        ft.Row(controls=title_controls, spacing=12, expand=True, wrap=True),
                        delete_btn
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER
                )

                trip_card = ft.ExpansionTile(
                    title=tile_title,
                    subtitle=ft.Text(f"Дати: {dates}", color=ft.colors.BLUE_300),
                    leading=ft.Icon(ft.icons.FLIGHT_TAKEOFF, color=ft.colors.BLUE_400),
                    controls_padding=20,
                    controls=[
                        flights_row,
                        ft.Divider(height=15, color="transparent"),
                        ft.Text("📍 Обов'язково відвідати (натисніть, щоб відкрити на карті):", weight=ft.FontWeight.W_500, color=ft.colors.GREY_300),
                        places_row,
                        ft.Divider(height=10, color="transparent"),
                        tip_container
                    ]
                )

                trips_list.controls.append(ft.Card(content=trip_card, elevation=3))

        except Exception as e:
            trips_list.controls.append(ft.Text(f"Помилка БД: {e}", color=ft.colors.RED))

        page.update()

    load_trips()

    return ft.View(
        "/trips",
        controls=[
            ft.AppBar(
                leading=ft.IconButton(ft.icons.ARROW_BACK, icon_color=ft.colors.WHITE, on_click=lambda e: page.go("/planner")),
                title=ft.Text("Мої збережені подорожі", color=ft.colors.WHITE, weight=ft.FontWeight.BOLD),
                bgcolor=ft.colors.BLUE_900,
                elevation=5
            ),
            ft.Container(
                expand=True,
                padding=ft.padding.symmetric(horizontal=40, vertical=25),
                content=trips_list
            )
        ]
    )