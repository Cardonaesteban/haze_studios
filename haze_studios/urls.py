from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from dashboard import views as dashboard_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    # Recuperación de contraseña
    path('recuperar-password/', dashboard_views.recuperar_password, name='recuperar_password'),
    path('recuperar-password/confirmar/<uuid:token>/', dashboard_views.recuperar_password_confirmar, name='recuperar_password_confirmar'),
    path('tienda/', include('tienda.urls')),
    path('', include('dashboard.urls')),
]