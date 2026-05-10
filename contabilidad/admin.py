from django.contrib import admin
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import path
from django.utils import timezone
from django.utils.html import format_html
from .models import Ingreso, Gasto, CostoFijo
import csv
from datetime import timedelta
from django.urls import reverse

# ==========================================
# VISTA DE RESUMEN CONTABLE
# ==========================================

def resumen_contable_view(request):
    """Vista para mostrar el resumen contable"""
    periodo = request.GET.get('periodo', 'mes')
    
    hoy = timezone.now().date()
    
    if periodo == 'dia':
        inicio = hoy
        fin = hoy + timedelta(days=1)
        titulo = "Resumen del día de hoy"
    elif periodo == 'semana':
        inicio = hoy - timedelta(days=hoy.weekday())
        fin = inicio + timedelta(days=7)
        titulo = "Resumen de esta semana"
    elif periodo == 'mes':
        inicio = hoy.replace(day=1)
        if inicio.month == 12:
            fin = inicio.replace(year=inicio.year + 1, month=1)
        else:
            fin = inicio.replace(month=inicio.month + 1)
        titulo = "Resumen de este mes"
    elif periodo == 'anio':
        inicio = hoy.replace(month=1, day=1)
        fin = inicio.replace(year=inicio.year + 1)
        titulo = "Resumen de este año"
    else:
        inicio = None
        fin = None
        titulo = "Resumen total histórico"

    # Calcular ingresos
    ingresos = Ingreso.objects.all()
    if inicio and fin:
        ingresos = ingresos.filter(fecha__date__gte=inicio, fecha__date__lt=fin)
    total_ingresos = ingresos.aggregate(total=Sum('monto'))['total']
    total_ingresos = float(total_ingresos) if total_ingresos else 0.0

    # Calcular gastos
    gastos = Gasto.objects.all()
    if inicio and fin:
        gastos = gastos.filter(fecha__date__gte=inicio, fecha__date__lt=fin)
    total_gastos = gastos.aggregate(total=Sum('monto'))['total']
    total_gastos = float(total_gastos) if total_gastos else 0.0

    # Costos fijos (simplificado)
    costos_fijos = CostoFijo.objects.all()
    total_costos_fijos = 0.0
    for cf in costos_fijos:
        total_costos_fijos += float(cf.monto)

    ganancia_neta = total_ingresos - total_gastos - total_costos_fijos

    # Últimos registros
    ultimos_ingresos = Ingreso.objects.all().order_by('-fecha')[:10]
    ultimos_gastos = Gasto.objects.all().order_by('-fecha')[:10]

    context = {
        'titulo': titulo,
        'periodo_actual': periodo,
        'total_ingresos': total_ingresos,
        'total_gastos': total_gastos,
        'total_costos_fijos': total_costos_fijos,
        'ganancia_neta': ganancia_neta,
        'ultimos_ingresos': ultimos_ingresos,
        'ultimos_gastos': ultimos_gastos,
        'periodos': [
            ('dia', 'Hoy'),
            ('semana', 'Esta semana'),
            ('mes', 'Este mes'),
            ('anio', 'Este año'),
            ('todo', 'Todo el historial'),
        ]
    }
    
    return render(request, 'admin/resumen_contable.html', context)


# ==========================================
# AGREGAR LA URL AL ADMIN
# ==========================================

# Guardar la función original de get_urls
original_get_urls = admin.site.get_urls

def get_urls_with_resumen():
    urls = original_get_urls()
    custom_urls = [
        path('resumen-contable/', admin.site.admin_view(resumen_contable_view), name='resumen_contable'),
    ]
    return custom_urls + urls

admin.site.get_urls = get_urls_with_resumen


# ==========================================
# ADMIN PARA INGRESOS
# ==========================================

@admin.register(Ingreso)
class IngresoAdmin(admin.ModelAdmin):
    list_display = ('id', 'fecha', 'monto', 'moneda', 'venta_link', 'descripcion')
    list_filter = ('moneda', 'fecha')
    search_fields = ('descripcion', 'venta__cliente__nombre')
    readonly_fields = ('fecha',)
    
    def venta_link(self, obj):
        if obj.venta:
            return format_html('<a href="/admin/ventas/venta/{}/">Venta #{}</a>', obj.venta.id, obj.venta.id)
        return "-"
    venta_link.short_description = "Venta asociada"


# ==========================================
# ADMIN PARA GASTOS
# ==========================================

@admin.register(Gasto)
class GastoAdmin(admin.ModelAdmin):
    list_display = ('id', 'fecha', 'tipo', 'monto', 'moneda', 'descripcion')
    list_filter = ('tipo', 'moneda', 'fecha')
    search_fields = ('descripcion',)
    readonly_fields = ('fecha',)


# ==========================================
# ADMIN PARA COSTOS FIJOS
# ==========================================

@admin.register(CostoFijo)
class CostoFijoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'monto', 'moneda', 'periodo', 'fecha_inicio')
    list_filter = ('periodo', 'moneda')
    search_fields = ('nombre',)


# ==========================================
# FUNCIONES DE EXPORTACIÓN
# ==========================================

def reporte_ingresos_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="ingresos_arkadya.csv"'
    writer = csv.writer(response)
    writer.writerow(['ID', 'Fecha', 'Monto', 'Moneda', 'Descripción'])
    for ingreso in queryset:
        writer.writerow([ingreso.id, ingreso.fecha, ingreso.monto, ingreso.moneda, ingreso.descripcion])
    return response
reporte_ingresos_csv.short_description = "Exportar ingresos a CSV"

def reporte_gastos_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="gastos_arkadya.csv"'
    writer = csv.writer(response)
    writer.writerow(['ID', 'Fecha', 'Tipo', 'Monto', 'Moneda', 'Descripción'])
    for gasto in queryset:
        writer.writerow([gasto.id, gasto.fecha, gasto.tipo, gasto.monto, gasto.moneda, gasto.descripcion])
    return response
reporte_gastos_csv.short_description = "Exportar gastos a CSV"

IngresoAdmin.actions = [reporte_ingresos_csv]
GastoAdmin.actions = [reporte_gastos_csv]


# ==========================================
# PERSONALIZACIÓN DEL ADMIN
# ==========================================

admin.site.site_header = "Arkadya Cobre - Administración"
admin.site.site_title = "Arkadya Cobre Admin"
admin.site.index_title = "Panel de Control"

from django.urls import reverse
from django.utils.html import format_html

# Agregar un enlace al dashboard en la página principal del admin
admin.site.index_title = "Panel de Control"

# Inyectar el enlace en el admin (opcional)
def dashboard_link():
    return format_html(
        '<div style="margin: 20px 0; text-align: center;">'
        '<a href="/dashboard/" style="background: #2d6a4f; color: white; '
        'padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">'
        '📊 Ver Dashboard de Análisis</a>'
        '</div>'
    )

# Esto es opcional - si quieres que aparezca automáticamente
# admin.site.index_template = "admin/index_with_dashboard.html"
