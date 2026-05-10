from django.shortcuts import render
from django.db import models
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth
from ventas.models import Venta, Cliente, DetalleVenta
from contabilidad.models import Ingreso, Gasto, CostoFijo
from datetime import datetime, timedelta
from calendar import month_name
from django.utils import timezone
import json
from productos.models import Producto


def dashboard_mejorado(request):
    """Dashboard con métricas avanzadas para Arkadya Cobre"""
    
    hoy = timezone.now().date()
    
    # ==========================================
    # MÉTRICAS DEL DÍA
    # ==========================================
    
    # Ventas del día (completadas)
    ventas_dia = Venta.objects.filter(
        estado='completado',
        fecha_pedido__date=hoy
    ).aggregate(
        total=Sum('total'),
        cantidad=Count('id')
    )
    
    total_ventas_dia = ventas_dia['total'] or 0
    cantidad_ventas_dia = ventas_dia['cantidad'] or 0
    
    # Reservas activas (pendiente + pagado)
    reservas_activas = Venta.objects.filter(
        estado__in=['pendiente', 'pagado']
    ).aggregate(total=Sum('total'))['total'] or 0
    
    # Pedidos pendientes de enviar (pagado)
    pedidos_por_enviar = Venta.objects.filter(
        estado='pagado',
        se_envio=False
    ).count()
    
    # Ticket promedio general
    total_ventas_general = Venta.objects.filter(
        estado='completado'
    ).aggregate(total=Sum('total'), cantidad=Count('id'))
    
    if total_ventas_general['cantidad'] and total_ventas_general['cantidad'] > 0:
        ticket_promedio = total_ventas_general['total'] / total_ventas_general['cantidad']
    else:
        ticket_promedio = 0
    
    # ==========================================
    # GRÁFICO DE ÚLTIMOS 7 DÍAS
    # ==========================================
    
    dias_semana = []
    ventas_ultimos_7 = []
    
    for i in range(6, -1, -1):
        fecha = hoy - timedelta(days=i)
        dias_semana.append(fecha.strftime('%d/%m'))
        
        total_dia = Venta.objects.filter(
            estado='completado',
            fecha_pedido__date=fecha
        ).aggregate(total=Sum('total'))['total'] or 0
        ventas_ultimos_7.append(float(total_dia))

    # ==========================================    
    # TOP 5 PRODUCTOS MÁS VENDIDOS (mes actual)
    # ==========================================
    inicio_mes = hoy.replace(day=1)
    
    try:
        top_productos = DetalleVenta.objects.filter(
            venta__fecha_pedido__gte=inicio_mes,
            venta__estado='completado'
        ).values('producto__nombre').annotate(
            total_vendido=Sum('cantidad')
        ).order_by('-total_vendido')[:5]
    except:
        top_productos = []


    # ==========================================
    # VENTAS POR ORIGEN (este mes)  ← AQUÍ VA EL CÓDIGO NUEVO
    # ==========================================
    
    origenes_labels = []
    origenes_montos = []
    
    ventas_por_origen = Venta.objects.filter(
        fecha_pedido__gte=inicio_mes
    ).values('origen').annotate(
        cantidad=Count('id'),
        total=Sum('total')
    )
    
    for item in ventas_por_origen:
        if item['origen'] == 'web':
            origenes_labels.append('🌐 Web')
        elif item['origen'] == 'instagram':
            origenes_labels.append('📷 Instagram')
        elif item['origen'] == 'whatsapp':
            origenes_labels.append('💬 WhatsApp')
        elif item['origen'] == 'presencial':
            origenes_labels.append('🏪 Presencial')
        else:
            origenes_labels.append(item['origen'])
        origenes_montos.append(float(item['total'] or 0))
    
    # ==========================================
    # ALERTAS DE STOCK
    # ==========================================
    
    productos_bajo_stock = Producto.objects.filter(
        stock__lte=models.F('stock_minimo'),
        stock_minimo__gt=0
    )[:10]
    
    # ==========================================
    # CONTEXTO PARA EL TEMPLATE
    # ==========================================
    
    context = {
        'total_ventas_dia': float(total_ventas_dia),
        'cantidad_ventas_dia': cantidad_ventas_dia,
        'reservas_activas': float(reservas_activas),
        'pedidos_por_enviar': pedidos_por_enviar,
        'ticket_promedio': float(ticket_promedio),
        'dias_semana': dias_semana,
        'ventas_ultimos_7': ventas_ultimos_7,
        'top_productos': top_productos,
        'productos_bajo_stock': productos_bajo_stock,
        'origenes_labels': origenes_labels,      # ← NUEVO
        'origenes_montos': origenes_montos,      # ← NUEVO
        'hoy': hoy.strftime('%d/%m/%Y'),
    }
    
    return render(request, 'admin/dashboard_mejorado.html', context)

def dashboard_analisis(request):
    # Obtener filtro de período (por defecto: mes actual)
    periodo = request.GET.get('periodo', 'mes')
    
    hoy = timezone.now().date()
    
    # Determinar el año seleccionado (para las ventas)
    anio_seleccionado = int(request.GET.get('anio', hoy.year))
    
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

    # ==========================================
    # 1. CALCULAR INGRESOS Y GASTOS (CONTABLE)
    # ==========================================
    
    # Ingresos
    ingresos = Ingreso.objects.all()
    if inicio and fin:
        ingresos = ingresos.filter(fecha__date__gte=inicio, fecha__date__lt=fin)
    total_ingresos = ingresos.aggregate(total=Sum('monto'))['total']
    total_ingresos = float(total_ingresos) if total_ingresos else 0.0

    # Gastos variables
    gastos = Gasto.objects.all()
    if inicio and fin:
        gastos = gastos.filter(fecha__date__gte=inicio, fecha__date__lt=fin)
    total_gastos = gastos.aggregate(total=Sum('monto'))['total']
    total_gastos = float(total_gastos) if total_gastos else 0.0

    # Costos fijos
    costos_fijos = CostoFijo.objects.all()
    total_costos_fijos = 0.0
    for cf in costos_fijos:
        total_costos_fijos += float(cf.monto)

    total_gastos_fijos = total_gastos + total_costos_fijos
    ganancia_neta = total_ingresos - total_gastos_fijos

    # Últimos registros
    ultimos_ingresos = Ingreso.objects.all().order_by('-fecha')[:10]
    ultimos_gastos = Gasto.objects.all().order_by('-fecha')[:10]

    # ==========================================
    # 2. VENTAS POR MES DEL AÑO (para gráficos)
    # ==========================================
    
    ventas_por_mes = Venta.objects.filter(
        fecha_pedido__year=anio_seleccionado
    ).annotate(
        mes=TruncMonth('fecha_pedido')
    ).values('mes').annotate(
        cantidad=Count('id'),
        total=Sum('total')
    ).order_by('mes')
    
    meses_nombres = [month_name[i] for i in range(1, 13)]
    cantidades_mes = [0] * 12
    ingresos_mes = [0.0] * 12
    
    for item in ventas_por_mes:
        mes_idx = item['mes'].month - 1
        cantidades_mes[mes_idx] = item['cantidad']
        ingresos_mes[mes_idx] = float(item['total']) if item['total'] else 0
    
    # ==========================================
    # 3. GASTOS POR MES DEL AÑO
    # ==========================================
    
    gastos_por_mes = Gasto.objects.filter(
        fecha__year=anio_seleccionado
    ).annotate(
        mes=TruncMonth('fecha')
    ).values('mes').annotate(
        total=Sum('monto')
    ).order_by('mes')
    
    gastos_mes = [0.0] * 12
    for item in gastos_por_mes:
        mes_idx = item['mes'].month - 1
        gastos_mes[mes_idx] = float(item['total']) if item['total'] else 0

    # ==========================================
    # 4. FILTRAR MESES CON ACTIVIDAD
    # ==========================================
    
    meses_filtrados = []
    cantidades_filtradas = []
    ingresos_filtrados = []
    gastos_filtrados = []
    
    for i in range(12):
        if cantidades_mes[i] > 0 or ingresos_mes[i] > 0 or gastos_mes[i] > 0:
            meses_filtrados.append(meses_nombres[i])
            cantidades_filtradas.append(cantidades_mes[i])
            ingresos_filtrados.append(ingresos_mes[i])
            gastos_filtrados.append(gastos_mes[i])
    
    # Si no hay datos, mostrar mensaje
    if not meses_filtrados:
        meses_filtrados = ['Sin datos']
        cantidades_filtradas = [0]
        ingresos_filtrados = [0]
        gastos_filtrados = [0]

    # ==========================================
    # 5. MÉTRICAS GENERALES
    # ==========================================
    
    total_clientes = Cliente.objects.count()
    
    # Nuevos clientes este mes
    inicio_mes_actual = hoy.replace(day=1)
    nuevos_clientes_mes = Cliente.objects.filter(
        fecha_registro__gte=inicio_mes_actual
    ).count()
    
    # Nuevos clientes mes anterior
    if hoy.month == 1:
        inicio_mes_anterior = hoy.replace(year=hoy.year-1, month=12, day=1)
    else:
        inicio_mes_anterior = hoy.replace(month=hoy.month-1, day=1)
    fin_mes_anterior = inicio_mes_actual - timedelta(days=1)
    nuevos_clientes_mes_anterior = Cliente.objects.filter(
        fecha_registro__gte=inicio_mes_anterior,
        fecha_registro__lte=fin_mes_anterior
    ).count()
    
    if nuevos_clientes_mes_anterior > 0:
        crecimiento_clientes = ((nuevos_clientes_mes - nuevos_clientes_mes_anterior) / nuevos_clientes_mes_anterior) * 100
    else:
        crecimiento_clientes = 100 if nuevos_clientes_mes > 0 else 0
    
    # Monto total de ventas (usando total, no monto_total)
    monto_total_ventas = Venta.objects.aggregate(total=Sum('total'))['total'] or 0
    
    # ==========================================
    # 6. TABLA MENSUAL
    # ==========================================
    
    tabla_mensual = []
    for mes in range(1, 13):
        ingresos_mes_valor = ingresos_mes[mes-1]
        gastos_mes_valor = gastos_mes[mes-1]
        ganancia_mes = ingresos_mes_valor - gastos_mes_valor
        
        tabla_mensual.append({
            'mes': month_name[mes],
            'ingresos': ingresos_mes_valor,
            'gastos': gastos_mes_valor,
            'ganancia': ganancia_mes,
            'ventas': cantidades_mes[mes-1]
        })

    # ==========================================
    # 5 TOP PRODUCTOS (corregido)
    # ==========================================
    
    try:
        top_productos = DetalleVenta.objects.filter(
            venta__fecha_pedido__year=anio_seleccionado,
            venta__estado='completado'
        ).values('producto__nombre').annotate(
            total_vendido=Sum('cantidad')
        ).order_by('-total_vendido')[:10]
    except:
        top_productos = []
    
    # ==========================================
    # 7. CLIENTES POR MES
    # ==========================================
    
    clientes_por_mes = Cliente.objects.filter(
        fecha_registro__year=anio_seleccionado
    ).annotate(
        mes=TruncMonth('fecha_registro')
    ).values('mes').annotate(
        cantidad=Count('id')
    ).order_by('mes')
    
    clientes_mes = [0] * 12
    for item in clientes_por_mes:
        mes_idx = item['mes'].month - 1
        clientes_mes[mes_idx] = item['cantidad']
    
    # ==========================================
    # 8. CLIENTES QUE COMPRARON VS TOTAL
    # ==========================================
    
    clientes_compraron = Venta.objects.values('cliente').distinct().count()
    tasa_conversion = (clientes_compraron / total_clientes * 100) if total_clientes > 0 else 0
    
    # ==========================================
    # 9. AÑOS DISPONIBLES
    # ==========================================
    
    años_disponibles = Venta.objects.dates('fecha_pedido', 'year').values_list('fecha_pedido__year', flat=True).distinct()
    if not años_disponibles:
        años_disponibles = [anio_seleccionado]
    
    # ==========================================
    # CONTEXTO FINAL
    # ==========================================
    
    context = {
        # Para el resumen contable (filtro por período)
        'titulo': titulo,
        'periodo_actual': periodo,
        'total_ingresos': total_ingresos,
        'total_gastos': total_gastos,
        'total_costos_fijos': total_costos_fijos,
        'total_gastos_fijos': total_gastos_fijos,
        'ganancia_neta': ganancia_neta,
        'ultimos_ingresos': ultimos_ingresos,
        'ultimos_gastos': ultimos_gastos,
        'periodos': [
            ('dia', 'Hoy'),
            ('semana', 'Esta semana'),
            ('mes', 'Este mes'),
            ('anio', 'Este año'),
            ('todo', 'Todo el historial'),
        ],
        
        # Para el dashboard de análisis (filtro por año)
        'anio_actual': anio_seleccionado,
        'años_disponibles': list(años_disponibles),
        'cantidades_mes': cantidades_filtradas,
        'ingresos_mes': ingresos_filtrados,
        'gastos_mes': gastos_filtrados,
        'meses_nombres': meses_filtrados,
        'total_clientes': total_clientes,
        'nuevos_clientes_mes': nuevos_clientes_mes,
        'crecimiento_clientes': round(crecimiento_clientes, 1),
        'monto_total_ventas': float(monto_total_ventas),
        'tabla_mensual': tabla_mensual,
        'top_productos': top_productos,
        'clientes_mes': clientes_mes,
        'clientes_compraron': clientes_compraron,
        'tasa_conversion': round(tasa_conversion, 1),
    }
    
    # Convertir datos a JSON para JavaScript
    context['meses_json'] = json.dumps(meses_filtrados)
    context['ventas_json'] = json.dumps(cantidades_filtradas)
    context['ingresos_json'] = json.dumps(ingresos_filtrados)
    context['gastos_json'] = json.dumps(gastos_filtrados)
    
    return render(request, 'admin/resumen_contable.html', context)
    
   


