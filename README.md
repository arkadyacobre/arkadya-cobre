# 🏺 Arkadya Cobre

Sistema de gestión integral para **Arkadya Cobre**, un emprendimiento de artesanía en cobre con base en Asunción, Paraguay.

## ✨ Características

- 🛒 **Catálogo de productos** con conversor de monedas (PYG, USD, EUR, ARS, BRL)
- 🛍️ **Carrito de compras** con validación de stock y checkout por WhatsApp
- 📊 **Dashboards** (Análisis financiero y métricas de ventas)
- 📦 **Gestión de stock** automática
- 💰 **Contabilidad** (ingresos, gastos, costos fijos)
- 📱 **Formulario móvil** para ventas rápidas desde redes sociales
- 📝 **Blog** con artículos informativos y lightbox para imágenes
- 📈 **Exportación a CSV** de todos los datos
- 🌐 **Desplegado en PythonAnywhere**

## 🛠️ Tecnologías utilizadas

- **Backend:** Django 6.0, Python 3.13
- **Frontend:** HTML5, CSS3, JavaScript (Chart.js)
- **Base de datos:** SQLite (local) / SQLite3 (producción)
- **Despliegue:** PythonAnywhere
- **Control de versiones:** Git + GitHub

## 🚀 Instalación local

```bash
# Clonar el repositorio
git clone https://github.com/arkadyacobre/arkadya-cobre.git
cd arkadya-cobre

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Instalar dependencias
pip install -r requirements.txt

# Migrar base de datos
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Ejecutar servidor
python manage.py runserver

🌐 Sitio web
https://arkadyacobre.pythonanywhere.com/

📞 Contacto
📧 Email: arkadya.cobre.py@gmail.com

📱 WhatsApp: +595 991519823

📸 Instagram: @arkadyacobre

📄 Estado del proyecto
✅ En producción | 🟡 En constante mejora

Desarrollado con ❤️ para Arkadya Cobre