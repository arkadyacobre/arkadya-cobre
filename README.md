# Arkadya Cobre

Sistema de gestion integral para **Arkadya Cobre**, un emprendimiento de artesania en cobre con base en Asuncion, Paraguay.

## Caracteristicas

- Catalogo de productos con conversor de monedas (PYG, USD, EUR, ARS, BRL).
- Carrito de compras con validacion de stock y checkout por WhatsApp.
- Dashboards con analisis financiero y metricas de ventas.
- Gestion de stock automatica.
- Contabilidad: ingresos, gastos y costos fijos.
- Formulario movil para ventas rapidas desde redes sociales.
- Blog con articulos informativos y lightbox para imagenes.
- Exportacion CSV desde el administrador.
- Deploy previsto en PythonAnywhere.

## Tecnologias

- Python 3.12.
- Django 6.0.5.
- SQLite local.
- HTML, CSS y JavaScript.

## Instalacion local

```powershell
cd C:\Users\seral\Desktop\arkadya-cobre

# Crear entorno virtual
python -m venv .venv

# Activar entorno virtual
.\.venv\Scripts\Activate.ps1

# Instalar dependencias
python -m pip install -r requirements.txt

# Aplicar migraciones
python manage.py migrate

# Verificar configuracion
python manage.py check

# Ejecutar servidor
python manage.py runserver
```

Si PowerShell bloquea la activacion del entorno virtual, tambien se puede ejecutar Python directamente:

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py runserver
```

## Variables de entorno

En desarrollo hay valores fallback para levantar el proyecto localmente. En produccion se deben definir:

```powershell
$env:DJANGO_SECRET_KEY="cambiar-por-una-clave-segura"
$env:TOKEN_VENTA_RAPIDA="cambiar-por-un-token-seguro"
```

En PythonAnywhere, configurar estas variables en el entorno de la aplicacion antes de reiniciar el sitio.

## Sitio web

https://arkadyacobre.pythonanywhere.com/

## Contacto

- Email: arkadya.cobre.py@gmail.com
- WhatsApp: +595 991519823
- Instagram: @arkadyacobre

## Backups

El archivo `backup.bat` automatiza copias locales de la base SQLite. Antes de ejecutar cambios de datos o despliegues, generar una copia de `db.sqlite3` y conservarla fuera del repositorio.
