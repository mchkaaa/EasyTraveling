import flet as ft
from views.login_view import get_login_view
from views.register_view import get_register_view
from views.planner_view import get_planner_view
from database import init_db

def main(page: ft.Page):
    init_db()
    page.title = "Travel Planner"
    page.window.width = 400
    page.window.height = 600

    def route_change(e):
        page.views.clear()
        
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