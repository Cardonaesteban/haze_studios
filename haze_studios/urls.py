from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # Ruta del panel de administración de Django
    path('admin/', admin.site.urls),

    # Ruta principal conectada a la aplicación local 'dashboard'
    path('', include('dashboard.urls')),
]