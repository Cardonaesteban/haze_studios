from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_cliente, name='tienda_login'),
    path('logout/', views.logout_cliente, name='tienda_logout'),
    path('inicio/', views.inicio, name='tienda_inicio'),
]
