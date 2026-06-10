# Haze Studios — Dashboard Admin en Django

Migración completa del dashboard admin de PHP + MySQLi a Django.

## Estructura del proyecto

```
haze_studios_django/
├── haze_studios/           # Configuración principal
│   ├── settings.py
│   └── urls.py
├── dashboard/              # App con todos los módulos
│   ├── models.py           # 7 modelos: Categoria, Proveedor, Disenador,
│   │                       #            Producto, Cliente, Pedido, Inventario
│   ├── views.py            # CRUD completo para cada módulo
│   ├── forms.py            # ModelForms con validación
│   ├── urls.py             # 30+ rutas
│   ├── migrations/
│   └── templates/
│       ├── dashboard/
│       │   ├── base.html   # Navbar + mensajes flash
│       │   ├── index.html  # Dashboard con stats y módulos
│       │   ├── confirmar_eliminar.html
│       │   ├── usuarios/   list.html + form.html
│       │   ├── productos/  list.html + form.html
│       │   ├── categorias/ list.html + form.html
│       │   ├── pedidos/    list.html + form.html
│       │   ├── inventario/ list.html + form.html
│       │   ├── proveedores/list.html + form.html
│       │   └── disenadores/list.html + form.html
│       └── registration/
│           └── login.html
├── static/
│   └── css/
│       └── haze.css        # CSS unificado (paleta original)
├── requirements.txt
└── manage.py
```

## Instalación y uso

### 1. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 2. Configurar base de datos

**Opción A — SQLite (por defecto, ideal para desarrollo):**
No requiere configuración adicional.

**Opción B — MySQL (igual que el proyecto PHP):**
En `haze_studios/settings.py`, descomenta el bloque MySQL y comenta el de SQLite:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'haze_studios',
        'USER': 'root',
        'PASSWORD': '',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
```
Luego instala el driver: `pip install mysqlclient`

### 3. Aplicar migraciones
```bash
python manage.py migrate
```

### 4. Crear superusuario (login del admin)
```bash
python manage.py createsuperuser
```

### 5. Correr el servidor
```bash
python manage.py runserver
```

Accede en: **http://127.0.0.1:8000/**

---

#hola

## Iniciar en otro pc con rol admin

Despues de clonar el proyecto ejecutar en la terminal:

py manage.py migrate
py manage.py setup_inicial
py manage.py runserver