import flet as ft
from api_service import search_flights  # Підключаємо нашу функцію для API

def get_planner_view(page: ft.Page):
    user_id = page.session.get("user_id")
    if not user_id:
        page.go("/login")
        return ft.View("/planner", [])

    # Оновлені поля під вимоги API Sky Scrapper
    origin_field = ft.TextField(label="Звідки (код, напр. LHR)", width=195)
    destination_field = ft.TextField(label="Куди (код, напр. CDG)", width=195)
    date_field = ft.TextField(label="Дата вильоту", hint_text="РРРР-ММ-ДД", width=400)

    results_container = ft.Column()

    def on_generate_click(e):
        # 1. Показуємо індикатор завантаження
        results_container.controls.clear()
        results_container.controls.append(
            ft.Text("⏳ Відправляємо запит до RapidAPI...", color=ft.colors.BLUE)
        )
        page.update()

        # 2. Передаємо дані з полів у нашу функцію
        api_result = search_flights(
            origin=origin_field.value,
            destination=destination_field.value,
            date=date_field.value
        )

        # 3. Виводимо "сиру" відповідь сервера на екран
        results_container.controls.clear()
        results_container.controls.append(
            ft.Text(f"Відповідь сервера:\n{api_result}", selectable=True)
        )
        page.update()

    generate_btn = ft.ElevatedButton(text="Згенерувати тур", on_click=on_generate_click, bgcolor=ft.colors.BLUE, color=ft.colors.WHITE)

    return ft.View(
        "/planner",
        controls=[
            ft.AppBar(title=ft.Text("EasyTraveling - Планувальник"), bgcolor=ft.colors.SURFACE_VARIANT),
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
                        date_field,
                        ft.Divider(height=10, color="transparent"),
                        
                        generate_btn,
                        ft.Divider(height=20),
                        
                        results_container
                    ]
                )
            )
        ]
    )