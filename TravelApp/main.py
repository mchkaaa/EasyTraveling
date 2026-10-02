import flet as ft
import re

def main(page: ft.Page):
    page.title = "Travel Planner"
    page.window.width = 400
    page.window.height = 600

    # Ця функція спрацьовує щоразу, коли змінюється адреса
    def route_change(e):
        page.views.clear()
        
       
        if page.route == "/login":
            # Зберігаємо поля в окремі змінні до того, як віддамо їх на екран
            email_field = ft.TextField(label="Email", width=300, prefix_icon=ft.icons.EMAIL)
            pass_field = ft.TextField(label="Пароль", width=300, password=True, can_reveal_password=True, prefix_icon=ft.icons.LOCK)

            
            def login_click(e):
                # Спочатку очищаємо старі повідомлення про помилки
                email_field.error_text = None
                pass_field.error_text = None

                email_pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'

                # Перевірки
                if not email_field.value:
                    email_field.error_text = "Введіть email"
                elif not re.match(email_pattern,email_field.value):
                    email_field.error_text = "Некоректний формат email"
                elif not pass_field.value:
                    pass_field.error_text = "Введіть пароль"
                elif len(pass_field.value)<8:
                    pass_field.error_text = "Пароль має містити мінімум 8 символів"
                elif not re.search(r"[!@#$%^&*(),.?\":{}|<>]", pass_field.value):
                    pass_field.error_text ="Додайте хоча б один спецсимвол (!@#$% та ін.)"
                else:
                    # Якщо поля заповнені, просто друкуємо це в термінал (тимчасово)
                    print(f"Авторизація успішна для: {email_field.value}")
                    # Пізніше замінимо print на page.go("/planner")

                # Наказуємо екрану оновитися, щоб показати червоний текст помилки (якщо він є)
                page.update()

            page.views.append(
                ft.View(
                    route="/login",
                    vertical_alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=20,
                    controls=[
                        ft.Icon(name=ft.icons.FLIGHT_TAKEOFF, size=80, color="#FFDDAF"),
                        ft.Text("EasyTraveling", size=40, color="#FFDDAF", weight=ft.FontWeight.BOLD),
                        ft.Text("Сплануйте свою ідеальну поїздку", size=16, color=ft.colors.GREY_400),
                        
                        # 3. Вставляємо наші змінні замість створення полів прямо тут
                        email_field,
                        pass_field,
                        
                        ft.ElevatedButton(
                            "Увійти", 
                            width=300, 
                            bgcolor="#FFDDAF", 
                            color=ft.colors.BLACK,
                            on_click=login_click  # 4. Прив'язуємо нашу функцію до кнопки
                        ),
                        ft.TextButton("Немає акаунту? Зареєструватися", on_click=lambda e: page.go("/register"))
                    ]
                )
            )
        
       
        elif page.route == "/register":
            name_field = ft.TextField(label="Ім'я", width=300, prefix_icon=ft.icons.PERSON)
            email_field = ft.TextField(label="Email", width=300, prefix_icon=ft.icons.EMAIL)
            pass_field = ft.TextField(label="Пароль", width=300, password=True, can_reveal_password=True, prefix_icon=ft.icons.LOCK)
            # Додаємо нове поле для підтвердження пароля
            pass_confirm_field = ft.TextField(label="Підтвердіть пароль", width=300, password=True, can_reveal_password=True, prefix_icon=ft.icons.LOCK_RESET)

            def register_click(e):
                # Очищаємо всі старі помилки
                name_field.error_text = None
                email_field.error_text = None
                pass_field.error_text = None
                pass_confirm_field.error_text = None

                # Шаблон для перевірки правильного email
                email_pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'

                # Каскад перевірок (виконується по черзі зверху вниз)
                if not name_field.value:
                    name_field.error_text = "Введіть ваше ім'я"
                elif re.search(r"[0-9!@#$%^&*(),.?\":{}|<>]", name_field.value):
                    name_field.error_text = "Ім'я не може містити цифри або спецсимволи"
                elif not re.match(email_pattern, email_field.value):
                    email_field.error_text = "Некоректний формат email"
                elif len(pass_field.value) < 8:
                    pass_field.error_text = "Пароль має містити мінімум 8 символів"
                elif not re.search(r"[!@#$%^&*(),.?\":{}|<>]", pass_field.value):
                    pass_field.error_text = "Додайте хоча б один спецсимвол (!@#$% та ін.)"
                elif pass_field.value != pass_confirm_field.value:
                    pass_confirm_field.error_text = "Паролі не співпадають"
                else:
                    print(f"Реєстрація успішна: {name_field.value}, {email_field.value}")
                    # page.go("/planner")

                page.update()

            page.views.append(
                ft.View(
                    route="/register",
                    vertical_alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=20,
                    controls=[
                        ft.Icon(name=ft.icons.FLIGHT_TAKEOFF, size=80, color="#FFDDAF"),
                        ft.Text("EasyTraveling", size=40, color="#FFDDAF", weight=ft.FontWeight.BOLD),
                        ft.Text("Створіть новий акаунт", size=16, color=ft.colors.GREY_400),
                        
                        name_field,
                        email_field,
                        pass_field,
                        pass_confirm_field, # Виводимо нове поле на екран
                        
                        ft.ElevatedButton(
                            "Зареєструватися", 
                            width=300, 
                            bgcolor="#FFDDAF", 
                            color=ft.colors.BLACK,
                            on_click=register_click
                        ),
                        ft.TextButton("Маєте акаунт? Увійти", on_click=lambda e: page.go("/login"))
                    ]
                )
            )

        page.update()

    
    page.on_route_change = route_change
    
    
    page.go("/login")

ft.app(target=main)