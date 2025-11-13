from django.urls import path
from . import views

urlpatterns = [
    path("", views.homepage, name="homepage"),
    path("cadastro/", views.cadastro, name="cadastro"),
    path("login/", views.login, name="login"),
    path("dashboard-reciclador/", views.dashboard_reciclador, name="reciclador"),
    path("dashboard-gerador/", views.dashboard_gerador, name="gerador"),
    path("logout/", views.logout, name="logout"),
    path("registro-material/", views.registrar_material, name="registro-material"),
]
