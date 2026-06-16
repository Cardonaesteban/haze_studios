## 🚀 Instalación y uso

### 🐳 Con Docker (recomendado)

**Requisito:** tener [Docker Desktop](https://www.docker.com/products/docker-desktop) instalado.

1. Clona el repositorio
```bash
   git clone https://github.com/Cardonaesteban/haze_studios
   cd haze-studios
```

2. Levanta los contenedores
```bash
   docker-compose up --build
```
## Si da error usar:
'''bash
    docker compose up
'''

3. Abre el navegador en `http://localhost:8000`

> La primera vez puede tardar unos minutos mientras Docker descarga las imágenes y aplica las migraciones automáticamente.

#### Detener el proyecto
```bash
docker-compose down
```

---

### 🐍 Sin Docker (manual)

**Requisitos:** Python 3.12 y MySQL instalados.

1. Clona el repositorio
```bash
   git clone https://github.com/Cardonaesteban/haze_studios
   cd haze-studios
```

2. Crea y activa el entorno virtual
```bash
   python -m venv venv
   venv\Scripts\activate
```

3. Instala las dependencias
```bash
   pip install -r requirements.txt
```

4. Configura la base de datos en `haze_studios/settings.py`
```python
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.mysql',
           'NAME': 'haze_db',
           'USER': 'haze_user',
           'PASSWORD': 'haze1234',
           'HOST': 'localhost',
           'PORT': '3306',
       }
   }
```

5. Aplica las migraciones y carga los datos iniciales
```bash
   python manage.py migrate
   python manage.py setup_inicial
```

6. Corre el servidor
```bash
   python manage.py runserver
```

7. Abre el navegador en `http://127.0.0.1:8000`