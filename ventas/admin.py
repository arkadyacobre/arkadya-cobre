from django.contrib import admin
from django.utils.html import format_html
from django.http import HttpResponse
from .models import Cliente, Venta, DetalleVenta
import csv

# ==========================================
# FUNCIONES DE EXPORTACIÓN
# ==========================================

def exportar_clientes_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="clientes_arkadya.csv"'
    writer = csv.writer(response)
    writer.writerow(['ID', 'Nombre', 'Teléfono', 'Localidad', 'Compras', 'Registro'])
    for c in queryset:
        writer.writerow([c.id, c.nombre, c.telefono, c.localidad, c.cantidad_compras, c.fecha_registro])
    return response
exportar_clientes_csv.short_description = "📊 Exportar clientes seleccionados a CSV"

def exportar_ventas_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="ventas_arkadya.csv"'
    writer = csv.writer(response)
    writer.writerow(['ID', 'Nro Pedido', 'Cliente', 'Estado', 'Total', 'Moneda', 'Fecha'])
    for v in queryset:
        writer.writerow([v.id, v.nro_pedido, v.cliente.nombre, v.get_estado_display(), 
                        v.total, v.moneda, v.fecha_pedido.strftime('%Y-%m-%d')])
    return response
exportar_ventas_csv.short_description = "📊 Exportar ventas seleccionadas a CSV"

def enviar_notificacion_manual(modeladmin, request, queryset):
    from django.http import HttpResponse
    from django.utils.html import escape

    enlaces = []
    for venta in queryset:
        if venta.estado != 'pendiente':
            url = venta.enviar_notificacion_whatsapp()
            if url:
                enlaces.append((venta.nro_pedido, url))

    if not enlaces:
        modeladmin.message_user(request, "No se generaron enlaces (ventas pendientes o sin datos).")
        return

    html = """
    <html>
    <head><title>Notificaciones WhatsApp</title></head>
    <body style="font-family: Arial, sans-serif; padding: 20px;">
        <h2>📱 Enlaces para enviar por WhatsApp</h2>
        <p>Haz clic en cada pedido para abrir WhatsApp con el mensaje predefinido.</p>
        <ul>
    """
    for pedido, url in enlaces:
        html += f'<li><a href="{escape(url)}" target="_blank">Pedido {escape(pedido)}</a></li>'
    html += """
        </ul>
        <p><a href="javascript:window.close()">Cerrar esta ventana</a></p>
    </body>
    </html>
    """
    return HttpResponse(html)

enviar_notificacion_manual.short_description = "📱 Enviar notificación por WhatsApp"

# ==========================================
# INLINE PARA DETALLES DE VENTA
# ==========================================

class DetalleVentaInline(admin.TabularInline):
    model = DetalleVenta
    extra = 1
    fields = ('producto', 'cantidad', 'precio_unitario', 'moneda')
    autocomplete_fields = ['producto']

# ==========================================
# ADMIN PARA CLIENTE
# ==========================================

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'telefono', 'localidad', 'cantidad_compras', 'fecha_registro')
    search_fields = ('nombre', 'telefono', 'localidad')
    list_filter = ('localidad', 'fecha_registro')
    ordering = ('-fecha_registro',)
    readonly_fields = ('fecha_registro', 'cantidad_compras')
    actions = [exportar_clientes_csv]

# ==========================================
# ADMIN PARA VENTA (UNA SOLA VEZ)
# ==========================================

@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nro_pedido', 'cliente', 'estado_coloreado', 'origen', 
                    'total', 'moneda', 'fecha_pedido')
    list_filter = ('estado', 'origen', 'moneda', 'fecha_pedido')
    search_fields = ('nro_pedido', 'cliente__nombre', 'cliente__telefono')
    ordering = ('-fecha_pedido',)
    readonly_fields = ('nro_pedido', 'fecha_pedido', 'fecha_actualizacion')
    inlines = [DetalleVentaInline]
    actions = [exportar_ventas_csv, enviar_notificacion_manual]
    autocomplete_fields = ['cliente']
    
    fieldsets = (
        ('Identificación', {
            'fields': ('nro_pedido', 'cliente', 'estado', 'origen')
        }),
        ('Montos', {
            'fields': ('moneda', 'subtotal', 'costo_envio', 'total')
        }),
        ('Envío y Pago', {
            'fields': ('metodo_pago', 'metodo_entrega', 'empresa_transporte', 'se_envio', 'facturado')
        }),
    )
    
    def estado_coloreado(self, obj):
        colores = {
            'pendiente': 'orange',
            'pagado': 'blue',
            'enviado': 'purple',
            'completado': 'green',
            'cancelado': 'red',
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colores.get(obj.estado, 'black'),
            obj.get_estado_display()
        )
    estado_coloreado.short_description = 'Estado'


# Nota: NO registrar Venta nuevamente aquí, ya que ya se hizo con el decorador @admin.register(Venta) arriba.