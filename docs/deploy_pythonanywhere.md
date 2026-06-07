# Deploy en PythonAnywhere

Notas para desplegar Arkadya Cobre sin mezclar archivos viejos con el codigo nuevo.

## Antes de desplegar

En local:

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
git status
```

Si hay cambios de modelos, crear y commitear las migraciones antes del deploy.

## Espacio en cuenta gratuita

La cuenta gratuita tiene poco espacio disponible. Evitar duplicar `venv`, `media`, `staticfiles` y backups grandes.

En PythonAnywhere:

```bash
du -sh ~
du -sh ~/arkadya-cobre/*
```

Limpiar caches seguros:

```bash
find ~/arkadya-cobre -type d -name "__pycache__" -prune -exec rm -rf {} \;
find ~/arkadya-cobre -type f -name "*.pyc" -delete
rm -rf ~/.cache/pip
```

## Deploy liviano desde ZIP de GitHub

Bajar el codigo a `/tmp`:

```bash
cd /tmp
rm -rf arkadya-cobre-deploy arkadya-cobre.zip arkadya-cobre-main
wget -O arkadya-cobre.zip https://github.com/arkadyacobre/arkadya-cobre/archive/refs/heads/main.zip
unzip arkadya-cobre.zip
mv arkadya-cobre-main arkadya-cobre-deploy
```

Importante: antes de copiar una app, borrar su carpeta de codigo anterior para no dejar migraciones viejas mezcladas. No borrar `db.sqlite3`, `media`, `venv` ni `staticfiles`.

```bash
cd ~/arkadya-cobre

rm -rf arkadya_system contabilidad productos tienda ventas templates

cp -a /tmp/arkadya-cobre-deploy/arkadya_system .
cp -a /tmp/arkadya-cobre-deploy/contabilidad .
cp -a /tmp/arkadya-cobre-deploy/productos .
cp -a /tmp/arkadya-cobre-deploy/tienda .
cp -a /tmp/arkadya-cobre-deploy/ventas .
cp -a /tmp/arkadya-cobre-deploy/templates .
cp /tmp/arkadya-cobre-deploy/manage.py .
cp /tmp/arkadya-cobre-deploy/requirements.txt .
```

Si existe carpeta `static` en el repo, copiarla tambien:

```bash
test -d /tmp/arkadya-cobre-deploy/static && cp -a /tmp/arkadya-cobre-deploy/static .
```

## Variables de entorno

En el archivo WSGI de PythonAnywhere, antes de `get_wsgi_application()`:

```python
import os

os.environ["DJANGO_SECRET_KEY"] = "clave-segura"
os.environ["TOKEN_VENTA_RAPIDA"] = "token-seguro"
```

## Verificacion

```bash
cd ~/arkadya-cobre
source venv/bin/activate
python manage.py check
python manage.py migrate
```

Si `migrate` falla por migraciones historicas mezcladas, no hacer reload a ciegas. Revisar que no hayan quedado migraciones antiguas por haber copiado carpetas encima.

Despues de verificar, usar el boton **Reload** en la pestana **Web** de PythonAnywhere.

## Regla para dos PCs

Antes de cambiar modelos o crear migraciones:

```bash
git checkout main
git pull origin main
git checkout -b codex/nombre-del-cambio
```

Solo una persona deberia crear migraciones para una misma app a la vez. Si dos PCs crean migraciones con el mismo numero, hay que resolverlo antes de subir a produccion.
