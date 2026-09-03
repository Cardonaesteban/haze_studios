# Imagen base de Python 3.12 liviana
FROM python:3.12-slim

# Instala dependencias del sistema necesarias para mysqlclient
RUN apt-get update && apt-get install -y \
    pkg-config \
    default-libmysqlclient-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Carpeta de trabajo dentro del contenedor
WORKDIR /app

# Copia las dependencias primero (optimización de caché)
COPY requirements.txt .

# Instala las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo el proyecto
COPY . .

# Puerto donde corre Django
EXPOSE 8000

# Junta estáticos y arranca el servidor (en runtime, no en build)
CMD python manage.py collectstatic --noinput && gunicorn haze_studios.wsgi:application --bind 0.0.0.0:8000