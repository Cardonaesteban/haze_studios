#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

# Recopilar archivos estáticos y crear la carpeta staticfiles
python manage.py collectstatic --no-input

# Aplicar migraciones a la base de datos PostgreSQL
python manage.py migrates