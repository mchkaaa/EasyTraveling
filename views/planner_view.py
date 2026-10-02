import flet as ft

def get_planner_view(page: ft.Page):
    return ft.View(
        route="/planner",
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=20,
        controls=[
            ft.Text("Головний екран планувальника", size=16, color=ft.colors.GREY_400),
            ft.ElevatedButton(
                "Вийти", 
                width=300, 
                bgcolor="#FFDDAF", 
                color=ft.colors.BLACK,
                on_click=lambda e: page.go("/login")
            )
        ]
    )