from django.contrib import admin
from .models import Producto, TasaCambio, Proveedor
from django.http import HttpResponse
import csv

# ==========================================
# FUNCIONES DE EXPORTACIÓN
# ==========================================

def exportar_productos_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="productos_arkadya.csv"'
    writer = csv.writer(response)
    writer.writerow(['ID', 'Nombre', 'Descripción', 'Stock', 'Stock Mínimo', 'Precio PYG'])
    for p in queryset:
        writer.writerow([p.id, p.nombre, p.descripcion, p.stock, p.stock_minimo, p.precio_pyg])
    return response
exportar_productos_csv.short_description = "📊 Exportar productos seleccionados a CSV"

def exportar_proveedores_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="proveedores_arkadya.csv"'
    writer = csv.writer(response)
    writer.writerow(['ID', 'Nombre', 'Empresa', 'Teléfono', 'Contacto'])
    for prov in queryset:
        writer.writerow([prov.id, prov.nombre, prov.empresa, prov.telefono, prov.contacto])
    return response
exportar_proveedores_csv.short_description = "📊 Exportar proveedores seleccionados a CSV"

# ==========================================
# ADMIN PARA PRODUCTO
# ==========================================

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'stock', 'stock_minimo', 'orden', 'precio_pyg')
    list_editable = ('orden',) 
    list_filter = ('stock_minimo',)
    search_fields = ('nombre',)
    actions = [exportar_productos_csv]

# ==========================================
# ADMIN PARA TASA DE CAMBIO
# ==========================================

@admin.register(TasaCambio)
class TasaCambioAdmin(admin.ModelAdmin):
    list_display = ('moneda', 'tasa', 'ultima_actualizacion')
    list_editable = ('tasa',)
    fields = ('moneda', 'tasa')

# ==========================================
# ADMIN PARA PROVEEDOR
# ==========================================

@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ('empresa', 'nombre', 'telefono')
    search_fields = ('empresa', 'nombre')
    actions = [exportar_proveedores_csv]