from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from tienda import views
from contabilidad.views import dashboard_analisis  # Importar la vista del dashboard
from productos.views import api_producto_precio
from ventas.views import venta_rapida, api_buscar_clientes, api_buscar_productos, api_guardar_venta_rapida
from contabilidad.views import dashboard_mejorado
from tienda.views import cuidados_cobre, beneficios_cobre, obtener_stock
from tienda.views import blog, detalle_articulo
from tienda.views import blog, blog_detalle 


urlpatterns = [
    path('', views.catalogo, name='catalogo'),
    path('envios/', views.politica_envios, name='envios'),
    path('pagos/', views.terminos_pago, name='pagos'),
    path('politicas/', views.politicas_ventas, name='politicas_ventas'),
    path('admin/api/producto-precio/<int:producto_id>/', api_producto_precio, name='api_producto_precio'),
    path('dashboard-mejorado/', dashboard_mejorado, name='dashboard_mejorado'),
    
    # Carrito
    path('agregar-al-carrito/', views.agregar_al_carrito, name='agregar_al_carrito'),
    path('obtener-carrito/', views.obtener_carrito, name='obtener_carrito'),
    path('actualizar-carrito/', views.actualizar_carrito, name='actualizar_carrito'),
    path('ver-carrito/', views.ver_carrito, name='ver_carrito'),
    path('finalizar-compra/', views.finalizar_compra_whatsapp, name='finalizar_compra'),
    
    # Admin y Dashboard
    path('admin/', admin.site.urls),
    path('dashboard/', dashboard_analisis, name='dashboard_analisis'),  # ← NUEVA RUTA FUERA DEL ADMIN

    # Ventas rápidas (móvil)
    path('venta-rapida/', venta_rapida, name='venta_rapida'),
    path('venta-rapida/api/buscar-clientes/', api_buscar_clientes, name='api_buscar_clientes'),
    path('venta-rapida/api/buscar-productos/', api_buscar_productos, name='api_buscar_productos'),
    path('venta-rapida/api/guardar-venta/', api_guardar_venta_rapida, name='api_guardar_venta'),

    #Cuidado de los Productos y Beneficios del Cobre
    path('cuidados/', cuidados_cobre, name='cuidados'),
    path('beneficios/', beneficios_cobre, name='beneficios'),

    #Sobre Nosotros, Aviso Legal, Privacidad.
    path('aviso-legal/', views.aviso_legal, name='aviso_legal'),
    path('privacidad/', views.privacidad, name='privacidad'),
    path('sobre-nosotros/', views.sobre_nosotros, name='sobre_nosotros'),

    #STOCK
    path('api/producto/<int:producto_id>/stock/', obtener_stock, name='obtener_stock'),

    #BLOG
    path('blog/', blog, name='blog'),
    path('blog/<slug:slug>/', detalle_articulo, name='detalle_articulo'),
    path('blog/', blog, name='blog'),
    path('blog/<int:articulo_id>/', blog_detalle, name='blog_detalle'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
