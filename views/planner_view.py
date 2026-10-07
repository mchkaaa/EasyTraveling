import flet as ft

def get_planner_view(page: ft.Page):
    # Перевірка авторизації (той самий фейсконтроль)
    user_id = page.session.get("user_id")
    if not user_id:
        page.go("/login")
        return ft.View("/planner", [])

    destination_field = ft.TextField(label="Куди хочете поїхати?", width=400)
    
    # Використовуємо звичайні текстові поля для дат (поки що)
    start_date_field = ft.TextField(label="Дата початку", hint_text="ДД-ММ-РРРР", width=195)
    end_date_field = ft.TextField(label="Дата завершення", hint_text="ДД-ММ-РРРР", width=195)

    #  Контейнер, куди ШІ буде віддавати згенеровані варіанти
    results_container = ft.Column()

    # 4. Дія при натисканні на кнопку
    def on_generate_click(e):
        # Очищаємо попередні результати
        results_container.controls.clear()
        
        # Тут згодом буде виклик реальних API та ШІ, а поки просто заглушка-індикатор
        results_container.controls.append(
            ft.Text(f"⏳ Шукаємо квитки та готелі для {destination_field.value}... Запускаємо ШІ-планувальник екскурсій...", color=ft.colors.BLUE)
        )
        page.update()

    generate_btn = ft.ElevatedButton(text="Згенерувати тур", on_click=on_generate_click, bgcolor=ft.colors.BLUE, color=ft.colors.WHITE)

    # 5. Збираємо все вікно до купи
    return ft.View(
        "/planner",
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=20,
        controls=[
            ft.AppBar(title=ft.Text("EasyTraveling - Планувальник"), bgcolor=ft.colors.SURFACE_VARIANT),
            ft.Container(
                padding=40,
                content=ft.Column(
                    controls=[
                        ft.Text("Сплануйте нову подорож", size=28, weight=ft.FontWeight.BOLD),
                        ft.Text("Введіть дані, а ми підберемо найкращі квитки, готелі та складемо програму.", color=ft.colors.GREY_700),
                        ft.Divider(height=10, color="transparent"),
                        
                        destination_field,
                        ft.Row([start_date_field, end_date_field], alignment=ft.MainAxisAlignment.START),
                        ft.Divider(height=10, color="transparent"),
                        
                        generate_btn,
                        ft.Divider(height=20),
                        
                        # Блок результатів розміщуємо під лінією
                        results_container
                    ]
                )
            )
        ]
    )