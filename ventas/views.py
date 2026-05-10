from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import models
from .models import Venta, DetalleVenta, Cliente, obtener_o_crear_cliente
from productos.models import Producto
from decimal import Decimal
import json
import urllib.parse

def verificar_token(request):
    """Verifica que el token de acceso sea válido"""
    token = request.GET.get('token', '')
    return token == settings.TOKEN_VENTA_RAPIDA


def venta_rapida(request):
    """Vista principal del formulario móvil para ventas rápidas"""
    if not verificar_token(request):
        return render(request, 'venta_rapida/error.html', {
            'mensaje': 'Acceso no autorizado. Token inválido.'
        })

    productos = Producto.objects.filter(stock__gt=0).order_by('nombre')
    return render(request, 'venta_rapida/index.html', {
        'productos': productos,
        'token': request.GET.get('token', '')
    })


@csrf_exempt
@require_http_methods(["POST"])
def api_buscar_clientes(request):
    """API para buscar clientes por nombre o teléfono"""
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
    """API para buscar productos por nombre"""
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
    """API para guardar la venta rápida"""
    if not verificar_token(request):
        return JsonResponse({'error': 'No autorizado'}, status=401)

    try:
        data = json.loads(request.body)

        # Obtener o crear cliente
        cliente_id = data.get('cliente_id')
        if cliente_id:
            cliente = get_object_or_404(Cliente, id=cliente_id)
        else:
            cliente = obtener_o_crear_cliente(
                nombre_completo=data.get('cliente_nombre'),
                telefono=data.get('cliente_telefono'),
                localidad=data.get('cliente_localidad', '')
            )

        # Crear venta
        venta = Venta.objects.create(
            cliente=cliente,
            estado='pendiente',
            origen=data.get('origen', 'whatsapp'),
            moneda='PYG',
            subtotal=Decimal(str(data.get('total', 0))),
            costo_envio=Decimal(str(data.get('costo_envio', 0))),
            total=Decimal(str(data.get('total', 0))),
            metodo_pago=data.get('metodo_pago', 'transferencia'),
            metodo_entrega=data.get('metodo_entrega', 'delivery'),
            se_envio=False,
            facturado=False
        )

        # Agregar detalles
        for item in data.get('productos', []):
            producto = get_object_or_404(Producto, id=item['producto_id'])
            DetalleVenta.objects.create(
                venta=venta,
                producto=producto,
                cantidad=int(item['cantidad']),
                precio_unitario=Decimal(str(item['precio_unitario'])),
                moneda='PYG'
            )

        # Incrementar contador de compras del cliente
        cliente.cantidad_compras += 1
        cliente.save()

        # Enviar WhatsApp al cliente
        mensaje = f"🏺 *ARKADYA COBRE - PEDIDO CONFIRMADO* 🏺\n\n"
        mensaje += f"📋 *Número de pedido:* {venta.nro_pedido}\n"
        mensaje += f"👤 *Cliente:* {cliente.nombre}\n"
        mensaje += f"📱 *Teléfono:* {cliente.telefono}\n\n"
        mensaje += "*📦 PRODUCTOS:*\n"

        for item in data.get('productos', []):
            mensaje += f"• {item['cantidad']} x {item['producto_nombre']} = ₲ {int(item['precio_unitario'] * item['cantidad']):,}\n"

        mensaje += f"\n*💰 TOTAL: ₲ {int(venta.total):,}*\n"
        mensaje += f"🚚 *Método de entrega:* {dict(Venta.ENTREGA).get(data.get('metodo_entrega'), data.get('metodo_entrega'))}\n\n"
        mensaje += "✅ *¡Gracias por tu compra!* Respondé este mensaje para coordinar envío y pago."

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

# Create your views here.

