import flet as ft
from views.login_view import get_login_view
from views.register_view import get_register_view
from views.planner_view import get_planner_view
from database import init_db
import os
from dotenv import load_dotenv

load_dotenv()

def main(page: ft.Page):
    init_db()
    page.title = "Travel Planner"
    page.window.width = 400
    page.window.height = 600

    def route_change(e):
        page.views.clear()

        # Перевіряємо, чи є користувач у пам'яті
        is_logged_in = page.client_storage.contains_key("user_id")

        # 1. Якщо користувач вже залогінений, але намагається зайти на сторінку входу/реєстрації або корінь
        if is_logged_in and page.route in ["/login", "/register", "/"]:
            page.go("/planner")
            return  # Обов'язково робимо return, щоб зупинити цю функцію

        # 2. Якщо користувач НЕ залогінений, але намагається потрапити в планувальник
        if not is_logged_in and page.route == "/planner":
            page.go("/login")
            return

        # 3. Якщо все добре, просто показуємо потрібну сторінку
        if page.route == "/login":
            page.views.append(get_login_view(page))
        elif page.route == "/register":
            page.views.append(get_register_view(page))
        elif page.route == "/planner":
            page.views.append(get_planner_view(page))
            
        page.update()

    page.on_route_change = route_change
    page.go("/login")

ft.app(target=main)