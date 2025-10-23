
from django.urls import path
from . import views

urlpatterns = [
    path('', views.homepage,name=''),
    path('cadastro/', views.cadastro,name='cadastro'),
    path('login/', views.login,name='login'),
    path('dashboard-reciclador/', views.dashboard_reciclador,name='reciclador'),
    path('dashboard-gerador/', views.dashboard_reciclador,name='gerador'),
    path('logout/', views.logout,name='logout'),
]

