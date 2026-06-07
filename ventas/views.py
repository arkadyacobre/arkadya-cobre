from decimal import Decimal
import json
import urllib.parse

from django.conf import settings
from django.db import models, transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from productos.models import Producto
from .models import Cliente, DetalleVenta, Venta, obtener_o_crear_cliente


def verificar_token(request):
    """Verifica que el token de acceso sea valido."""
    token = request.GET.get('token', '')
    return token == settings.TOKEN_VENTA_RAPIDA


def venta_rapida(request):
    """Vista principal del formulario movil para ventas rapidas."""
    if not verificar_token(request):
        return render(request, 'venta_rapida/error.html', {
            'mensaje': 'Acceso no autorizado. Token invalido.'
        })

    productos = Producto.objects.filter(stock__gt=0).order_by('nombre')
    return render(request, 'venta_rapida/index.html', {
        'productos': productos,
        'token': request.GET.get('token', '')
    })


@csrf_exempt
@require_http_methods(["POST"])
def api_buscar_clientes(request):
    """API para buscar clientes por nombre o telefono."""
    if not verificar_token(request):
        return JsonResponse({'error': 'No autorizado'}, status=401)

    termino = request.POST.get('termino', '')
    if len(termino) < 2:
        return JsonResponse({'clientes': []})

    clientes = Cliente.objects.filter(
        models.Q(nombre__icontains=termino) | models.Q(telefono__icontains=termino)
    )[:10]

    resultados = [{
        'id': c.id,
        'nombre': c.nombre,
        'telefono': c.telefono,
        'localidad': c.localidad
    } for c in clientes]

    return JsonResponse({'clientes': resultados})


@csrf_exempt
@require_http_methods(["POST"])
def api_buscar_productos(request):
    """API para buscar productos por nombre."""
    if not verificar_token(request):
        return JsonResponse({'error': 'No autorizado'}, status=401)

    termino = request.POST.get('termino', '')
    if len(termino) < 2:
        return JsonResponse({'productos': []})

    productos = Producto.objects.filter(
        nombre__icontains=termino,
        stock__gt=0
    )[:10]

    resultados = [{
        'id': p.id,
        'nombre': p.nombre,
        'precio': float(p.precio_pyg),
        'stock': p.stock
    } for p in productos]

    return JsonResponse({'productos': resultados})


@csrf_exempt
@require_http_methods(["POST"])
def api_guardar_venta_rapida(request):
    """API para guardar la venta rapida."""
    if not verificar_token(request):
        return JsonResponse({'error': 'No autorizado'}, status=401)

    try:
        data = json.loads(request.body)
        productos_solicitados = data.get('productos', [])
        if not productos_solicitados:
            return JsonResponse({'success': False, 'error': 'La venta no tiene productos.'}, status=400)

        with transaction.atomic():
            cliente_id = data.get('cliente_id')
            if cliente_id:
                cliente = get_object_or_404(Cliente, id=cliente_id)
            else:
                cliente = obtener_o_crear_cliente(
                    nombre_completo=data.get('cliente_nombre'),
                    telefono=data.get('cliente_telefono'),
                    localidad=data.get('cliente_localidad', '')
                )

            detalles = []
            subtotal = Decimal('0')
            for item in productos_solicitados:
                producto = get_object_or_404(
                    Producto.objects.select_for_update(),
                    id=item['producto_id']
                )
                cantidad = int(item['cantidad'])
                if cantidad < 1:
                    return JsonResponse({'success': False, 'error': 'La cantidad debe ser mayor a cero.'}, status=400)
                if not producto.hay_stock(cantidad):
                    return JsonResponse({
                        'success': False,
                        'error': f"No hay suficiente stock para {producto.nombre}. Disponible: {producto.stock}."
                    }, status=400)

                precio_unitario = producto.precio_pyg
                subtotal += precio_unitario * cantidad
                detalles.append({
                    'producto': producto,
                    'cantidad': cantidad,
                    'precio_unitario': precio_unitario,
                })

            costo_envio = Decimal(str(data.get('costo_envio', 0) or 0))
            total = subtotal + costo_envio

            venta = Venta.objects.create(
                cliente=cliente,
                estado='pendiente',
                origen=data.get('origen', 'whatsapp'),
                moneda='PYG',
                subtotal=subtotal,
                costo_envio=costo_envio,
                total=total,
                metodo_pago=data.get('metodo_pago', 'transferencia'),
                metodo_entrega=data.get('metodo_entrega', 'delivery'),
                se_envio=False,
                facturado=False
            )

            for detalle in detalles:
                DetalleVenta.objects.create(
                    venta=venta,
                    producto=detalle['producto'],
                    cantidad=detalle['cantidad'],
                    precio_unitario=detalle['precio_unitario'],
                    moneda='PYG'
                )

            cliente.cantidad_compras += 1
            cliente.save()

        mensaje = "*ARKADYA COBRE - PEDIDO CONFIRMADO*\n\n"
        mensaje += f"*Numero de pedido:* {venta.nro_pedido}\n"
        mensaje += f"*Cliente:* {cliente.nombre}\n"
        mensaje += f"*Telefono:* {cliente.telefono}\n\n"
        mensaje += "*PRODUCTOS:*\n"

        for detalle in detalles:
            subtotal_detalle = detalle['precio_unitario'] * detalle['cantidad']
            mensaje += f"- {detalle['cantidad']} x {detalle['producto'].nombre} = PYG {int(subtotal_detalle):,}\n"

        mensaje += f"\n*TOTAL: PYG {int(venta.total):,}*\n"
        mensaje += f"*Metodo de entrega:* {dict(Venta.ENTREGA).get(data.get('metodo_entrega'), data.get('metodo_entrega'))}\n\n"
        mensaje += "Gracias por tu compra. Responde este mensaje para coordinar envio y pago."

        mensaje_codificado = urllib.parse.quote(mensaje)
        whatsapp_url = f"https://wa.me/{cliente.telefono.replace('+', '')}?text={mensaje_codificado}"

        return JsonResponse({
            'success': True,
            'venta_id': venta.id,
            'nro_pedido': venta.nro_pedido,
            'whatsapp_url': whatsapp_url
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
