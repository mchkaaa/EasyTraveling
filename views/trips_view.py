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
            cursor.execute(
                "SELECT id, origin, destination, dates, plan_data FROM saved_trips WHERE user_id = ? ORDER BY id DESC",
                (user_id,)
            )
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
                page.update()
                return

            for row in rows:
                trip_id, origin, dest, dates, plan_data_str = row
                
                try:
                    plan_data = json.loads(plan_data_str)
                except Exception:
                    continue  # Пропускаємо пошкоджені записи
                
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
                    bgcolor=ft.colors.AMBER_100,
                    padding=15,
                    border_radius=10,
                    content=ft.Row([
                        ft.Icon(ft.icons.LIGHTBULB, color=ft.colors.AMBER_700),
                        ft.Text(plan_data.get("tip", ""), color=ft.colors.BLACK87, expand=True)
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
                            conn = sqlite3.connect("travel.db")
                            cursor = conn.cursor()
                            cursor.execute("DELETE FROM saved_trips WHERE id = ?", (tid,))
                            conn.commit()
                            conn.close()
                            
                            close_dlg(e)
                            load_trips()  # Оновлюємо список турів

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
                        
                        # Відкриття діалогу з підтримкою нових і старих версій Flet
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

                # Розміщуємо заголовок та кнопку в одному Row, щоб ExpansionTile не блокував натискання
                tile_title = ft.Row(
                    controls=[
                        ft.Text(f"{origin} ➔ {dest}", weight=ft.FontWeight.BOLD, size=18, expand=True),
                        delete_btn
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER
                )

                # Створюємо картку, що розгортається вниз
                trip_card = ft.ExpansionTile(
                    title=tile_title,
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
        
        page.update()

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