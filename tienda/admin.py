from django.contrib import admin
from .models import (
    TokenRecuperacionCliente,
    Favorito,
    Personalizacion,
    PrendaComunidad,
    ComentarioComunidad,
    ReaccionComunidad,
)


@admin.register(TokenRecuperacionCliente)
class TokenRecuperacionClienteAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'token', 'creado', 'usado')
    list_filter = ('usado', 'creado')
    search_fields = ('cliente__correo', 'token')
    readonly_fields = ('token', 'creado')


@admin.register(Favorito)
class FavoritoAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'producto', 'prenda_comunidad', 'fecha_agregado')
    list_filter = ('fecha_agregado',)
    search_fields = ('cliente__nombre', 'cliente__correo', 'producto__nombre', 'prenda_comunidad__nombre')
    readonly_fields = ('fecha_agregado',)


@admin.register(Personalizacion)
class PersonalizacionAdmin(admin.ModelAdmin):
    list_display = ('nombre_personalizacion', 'cliente', 'producto', 'tipo', 'talla', 'color', 'estado', 'fecha_creacion')
    list_filter = ('estado', 'tipo', 'talla', 'color')
    search_fields = ('nombre_personalizacion', 'cliente__nombre', 'producto__nombre')
    readonly_fields = ('fecha_creacion',)


class ComentarioComunidadInline(admin.TabularInline):
    model = ComentarioComunidad
    extra = 0
    readonly_fields = ('fecha_publicacion', 'fecha_edicion')


@admin.register(PrendaComunidad)
class PrendaComunidadAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'autor', 'color', 'talla', 'estado', 'fecha_publicacion')
    list_filter = ('estado', 'color', 'talla', 'estampado')
    search_fields = ('nombre', 'autor__nombre', 'autor__correo', 'descripcion')
    readonly_fields = ('fecha_publicacion', 'fecha_actualizacion')
    inlines = [ComentarioComunidadInline]


@admin.register(ComentarioComunidad)
class ComentarioComunidadAdmin(admin.ModelAdmin):
    list_display = ('prenda', 'autor', 'editado', 'fecha_publicacion')
    list_filter = ('editado', 'fecha_publicacion')
    search_fields = ('prenda__nombre', 'autor__nombre', 'contenido')
    readonly_fields = ('fecha_publicacion', 'fecha_edicion')


@admin.register(ReaccionComunidad)
class ReaccionComunidadAdmin(admin.ModelAdmin):
    list_display = ('prenda', 'cliente', 'fecha_creacion')
    list_filter = ('fecha_creacion',)
    search_fields = ('prenda__nombre', 'cliente__nombre')
    readonly_fields = ('fecha_creacion',)
