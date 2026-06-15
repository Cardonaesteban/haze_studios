
## Instalación y uso

### 1. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 2. Configurar base de datos
 MySQL 
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


## Iniciar en otro pc con rol admin

Despues de clonar el proyecto ejecutar en la terminal:

py manage.py migrate
py manage.py setup_inicial
py manage.py runserver

# Crear venv nuevo (Siempre nuevo)

python -m venv venv

Activarlo

venv\Scripts\activate

Instalar todo el proyecto

pip install -r requirements.txt

Migrar base de datos

python manage.py migrate

# Iniciar en otro pc
Instalar MariaDB 11.4 
Copiar el proyecto — con git o copiando la carpeta
Recrear el venv e instalar dependencias:

python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate