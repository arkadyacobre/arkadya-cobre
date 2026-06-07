from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.db import transaction
from productos.models import Producto, TasaCambio
from ventas.models import Venta, DetalleVenta, obtener_o_crear_cliente
from .models import Articulo
from decimal import Decimal
import json


# ==========================================
# FUNCIÓN PARA FORMATEAR PRECIOS
# ==========================================

def formatear_precio(valor):
    """Convierte 85000 a '85.000'"""
    try:
        entero = int(float(valor))
        partes = f"{entero:,}".split(',')
        return '.'.join(partes)
    except:
        return str(valor)


# ==========================================
# VISTA DEL CATÁLOGO PRINCIPAL
# ==========================================

def catalogo(request):
    # Obtener categoría seleccionada
    categoria_seleccionada = request.GET.get('cat')
    moneda = request.GET.get('moneda', 'PYG')
    
    # Definir orden personalizado de las categorías para el dropdown
    orden_categorias = [
        ('vasos', 'Vasos'),
        ('botellas', 'Botellas'),
        ('pulseras', 'Pulseras'),
        ('anillos', 'Anillos'),
        ('brazaletes', 'Brazaletes'),
        ('cadenas', 'Cadenas'),
        ('aros', 'Aros'),
        ('diademas', 'Diademas'),
        ('tobilleras', 'Tobilleras'),
        ('limpia_lengua', 'Limpia lengua'),
        ('dispenser', 'Dispenser de agua'),
        ('jarra', 'Jarra'),
        ('piramides', 'Pirámides'),
        ('espirales_mano', 'Espirales de mano'),
        ('pendulos', 'Péndulos'),
        ('energizador_agua', 'Energizador de agua'),
    ]
    
    # Filtrar productos
    productos = Producto.objects.all().order_by('orden', 'id')
    if categoria_seleccionada:
        productos = productos.filter(categoria=categoria_seleccionada)
    else:
        # Si no hay filtro, mostrar solo productos destacados
        productos = productos.filter(destacado=True)
    
    # Obtener tasas de cambio
    tasas = {}
    for tasa_obj in TasaCambio.objects.all():
        tasas[tasa_obj.moneda] = float(tasa_obj.tasa)
    
    catalogo_lista = []
    for producto in productos:
        precio_pyg = float(producto.precio_pyg)
        
        # Convertir según la moneda seleccionada
        if moneda == 'PYG':
            precio_convertido = precio_pyg
            simbolo = '₲'
        elif moneda == 'USD':
            precio_convertido = precio_pyg / tasas.get('USD', 7500)
            simbolo = 'USD $'
        elif moneda == 'EUR':
            precio_convertido = precio_pyg / tasas.get('EUR', 8000)
            simbolo = '€'
        elif moneda == 'ARS':
            precio_convertido = precio_pyg / tasas.get('ARS', 15)
            simbolo = 'ARS $'
        elif moneda == 'BRL':
            precio_convertido = precio_pyg / tasas.get('BRL', 1400)
            simbolo = 'R$'
        else:
            precio_convertido = precio_pyg
            simbolo = '₲'
        
        precio_formateado = f"{simbolo} {formatear_precio(precio_convertido)}"
        
        catalogo_lista.append({
            'producto': producto,
            'precio': precio_formateado,
            'precio_original': precio_pyg
        })
    
    # Obtener carrito actual para el contador
    carrito = request.session.get('carrito', {})
    total_items = sum(item['cantidad'] for item in carrito.values())
    
    return render(request, 'catalogo.html', {
        'catalogo': catalogo_lista,
        'moneda_actual': moneda,
        'categorias': orden_categorias,          # lista de tuplas para el dropdown
        'categoria_actual': categoria_seleccionada,
        'total_carrito_items': total_items,
    })


# ==========================================
# VISTAS DEL CARRITO DE COMPRAS
# ==========================================

def agregar_al_carrito(request):
    """Agrega un producto al carrito (vía AJAX)"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            producto_id = str(data.get('producto_id'))
            nombre = data.get('nombre')
            precio = float(data.get('precio', 0))
            cantidad = int(data.get('cantidad', 1))
            moneda = data.get('moneda', 'PYG')

    # Validar stock
            try:
                producto = Producto.objects.get(id=producto_id)
                if not producto.hay_stock(cantidad):
                    return JsonResponse({'success': False, 'error': 'No hay suficiente stock disponible'}, status=400)
            except Producto.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Producto no encontrado'}, status=400)           
            
            # Obtener carrito de la sesión
            carrito = request.session.get('carrito', {})
            
            if producto_id in carrito:
                # Si ya existe, aumentar cantidad
                cantidad_total = carrito[producto_id]['cantidad'] + cantidad
                if not producto.hay_stock(cantidad_total):
                    return JsonResponse({'success': False, 'error': 'No hay suficiente stock disponible'}, status=400)
                carrito[producto_id]['cantidad'] += cantidad
            else:
                # Si no existe, agregar
                carrito[producto_id] = {
                    'id': producto_id,
                    'nombre': nombre,
                    'precio': precio,
                    'cantidad': cantidad,
                    'moneda': moneda,
                }
            
            # Guardar carrito en la sesión
            request.session['carrito'] = carrito
            request.session.modified = True
            
            total_items = sum(item['cantidad'] for item in carrito.values())
            
            return JsonResponse({'success': True, 'total_items': total_items})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    return JsonResponse({'success': False}, status=400)


def obtener_carrito(request):
    """Devuelve el contenido actual del carrito"""
    carrito = request.session.get('carrito', {})
    items = list(carrito.values())
    total_items = sum(item['cantidad'] for item in items)
    total_precio = sum(item['precio'] * item['cantidad'] for item in items)
    
    return JsonResponse({
        'items': items,
        'total_items': total_items,
        'total_precio': total_precio,
    })


def actualizar_carrito(request):
    """Actualiza cantidades o elimina items del carrito"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            producto_id = str(data.get('producto_id'))
            accion = data.get('accion')
            
            carrito = request.session.get('carrito', {})
            
            if accion == 'increase':
                if producto_id in carrito:
                    try:
                        producto = Producto.objects.get(id=producto_id)
                        cantidad_total = carrito[producto_id]['cantidad'] + 1
                        if not producto.hay_stock(cantidad_total):
                            return JsonResponse({'success': False, 'error': 'No hay suficiente stock disponible'}, status=400)
                    except Producto.DoesNotExist:
                        return JsonResponse({'success': False, 'error': 'Producto no encontrado'}, status=400)
                    carrito[producto_id]['cantidad'] += 1
            elif accion == 'decrease':
                if producto_id in carrito:
                    if carrito[producto_id]['cantidad'] > 1:
                        carrito[producto_id]['cantidad'] -= 1
                    else:
                        del carrito[producto_id]
            elif accion == 'remove':
                if producto_id in carrito:
                    del carrito[producto_id]
            
            request.session['carrito'] = carrito
            request.session.modified = True
            
            total_items = sum(item['cantidad'] for item in carrito.values())
            total_precio = sum(item['precio'] * item['cantidad'] for item in carrito.values())
            
            return JsonResponse({
                'success': True,
                'total_items': total_items,
                'total_precio': total_precio,
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    return JsonResponse({'success': False}, status=400)


def ver_carrito(request):
    """Muestra la página del carrito de compras"""
    carrito = request.session.get('carrito', {})
    items = list(carrito.values())
    total_precio = sum(item['precio'] * item['cantidad'] for item in items)
    moneda = request.GET.get('moneda', 'PYG')
    
    return render(request, 'carrito.html', {
        'carrito': items,
        'total_precio': total_precio,
        'moneda_actual': moneda,
    })


def finalizar_compra_whatsapp_legacy(request):
    """Guarda el pedido en la base de datos y envía WhatsApp"""
    carrito = request.session.get('carrito', {})
    
    if not carrito:
        return redirect('catalogo')
    
    if request.method == 'POST':
        # Obtener datos del formulario
        nombre = request.POST.get('nombre')
        telefono = request.POST.get('telefono')
        localidad = request.POST.get('localidad', '')
        metodo_pago = request.POST.get('metodo_pago', 'transferencia')
        metodo_entrega = request.POST.get('metodo_entrega', 'delivery')
        
        # Verificar stock antes de procesar
        errores = []
        for item in carrito.values():
            producto = Producto.objects.get(id=item['id'])
            if not producto.hay_stock(item['cantidad']):
                errores.append(f"{producto.nombre} (solicitado: {item['cantidad']}, disponible: {producto.stock})")

        if errores:
            return render(request, 'finalizar_compra.html', {
                'carrito': carrito,
                'errores_stock': errores,
                'mensaje_error': 'No hay suficiente stock para algunos productos. Por favor, ajusta las cantidades.'
            })

        # Crear o actualizar cliente
        cliente = obtener_o_crear_cliente(nombre, telefono, localidad)
        
        # Obtener moneda (del primer producto del carrito)
        primer_item = list(carrito.values())[0]
        moneda = primer_item.get('moneda', 'PYG')
        
        # Calcular total en PYG
        total_pyg = 0
        detalles = []
        for item in carrito.values():
            producto_id = item['id']
            cantidad = item['cantidad']
            precio_original = Decimal(str(item['precio']))
            
            # Obtener producto real de la base de datos
            try:
                producto = Producto.objects.get(id=producto_id)
                precio_pyg = producto.precio_pyg
            except Producto.DoesNotExist:
                precio_pyg = precio_original
            
            subtotal_pyg = precio_pyg * cantidad
            total_pyg += subtotal_pyg
            
            detalles.append({
                'producto': producto,
                'cantidad': cantidad,
                'precio_unitario': precio_pyg,
                'moneda': 'PYG'
            })

        # ==========================================
        # VALIDACIÓN FINAL DE STOCK (CRÍTICA)
        # ==========================================
        errores_stock = []
        for item in carrito.values():
            producto = Producto.objects.get(id=item['id'])
            if not producto.hay_stock(item['cantidad']):
                errores_stock.append(f"{producto.nombre} (solicitado: {item['cantidad']}, disponible: {producto.stock})")

        if errores_stock:
            messages.error(request, f"No hay suficiente stock para completar el pedido: {', '.join(errores_stock)}")
            return redirect('ver_carrito')
        
        # Crear la venta
        venta = Venta.objects.create(
            cliente=cliente,
            estado='pendiente',
            origen='web',
            moneda=moneda,
            subtotal=total_pyg,
            costo_envio=0,
            total=total_pyg,
            metodo_pago=metodo_pago,
            metodo_entrega=metodo_entrega,
            se_envio=False,
            facturado=False
        )
        
        # Agregar detalles de venta
        for detalle in detalles:
            DetalleVenta.objects.create(
                venta=venta,
                producto=detalle['producto'],
                cantidad=detalle['cantidad'],
                precio_unitario=detalle['precio_unitario'],
                moneda='PYG'
            )
        
        # Incrementar contador de compras del cliente
        cliente.cantidad_compras += 1
        cliente.save()
        
        # Limpiar carrito
        request.session['carrito'] = {}
        request.session.modified = True
        
        # Construir mensaje de WhatsApp
        mensaje = f"🏺 *ARKADYA COBRE - PEDIDO CONFIRMADO* 🏺\n\n"
        mensaje += f"📋 *Número de pedido:* {venta.nro_pedido}\n"
        mensaje += f"👤 *Cliente:* {cliente.nombre}\n"
        mensaje += f"📱 *Teléfono:* {cliente.telefono}\n"
        mensaje += f"📍 *Localidad:* {cliente.localidad}\n\n"
        mensaje += "*📦 PRODUCTOS:*\n"
        
        for detalle in detalles:
            mensaje += f"• {detalle['cantidad']} x {detalle['producto'].nombre} = ₲ {detalle['precio_unitario'] * detalle['cantidad']:,.0f}\n"
        
        mensaje += f"\n*💰 TOTAL: ₲ {total_pyg:,.0f}*\n"
        mensaje += f"💳 *Método de pago:* {dict(Venta.METODO_PAGO).get(metodo_pago, metodo_pago)}\n"
        mensaje += f"🚚 *Método de entrega:* {dict(Venta.ENTREGA).get(metodo_entrega, metodo_entrega)}\n\n"
        mensaje += "✅ *¡Gracias por tu compra!*\n"
        mensaje += "Nos pondremos en contacto para coordinar el envío y pago.\n\n"
        mensaje += f"📞 *WhatsApp:* +595 991519823\n"
        mensaje += f"📸 *Instagram:* @arkadyacobre"
        
        import urllib.parse
        mensaje_codificado = urllib.parse.quote(mensaje)
        whatsapp_url = f"https://wa.me/595991519823?text={mensaje_codificado}"
        
        return redirect(whatsapp_url)
    
    # Si es GET, mostrar formulario para completar datos
    return render(request, 'finalizar_compra.html', {'carrito': carrito})


# ==========================================
# VISTAS DE PÁGINAS INFORMATIVAS
# ==========================================

def politica_envios(request):
    return render(request, 'envios.html')


def terminos_pago(request):
    return render(request, 'pagos.html')


def politicas_ventas(request):
    return render(request, 'politicas_ventas.html')


def cuidados_cobre(request):
    return render(request, 'cuidados.html')


def beneficios_cobre(request):
    return render(request, 'beneficios.html')

def sobre_nosotros(request):
    return render(request, 'sobre-nosotros.html')

def aviso_legal(request):
    return render(request, 'aviso-legal.html')

def privacidad(request):
    return render(request, 'privacidad.html')

# ==========================================
#  STOCK
# ==========================================

def obtener_stock(request, producto_id):
    try:
        producto = Producto.objects.get(id=producto_id)
        return JsonResponse({'stock': producto.stock})
    except Producto.DoesNotExist:
        return JsonResponse({'error': 'Producto no encontrado'}, status=404)

# ==========================================
#  BLOG
# ==========================================

def blog(request):
    articulos = Articulo.objects.filter(publicado=True).order_by('orden')
    return render(request, 'blog.html', {'articulos': articulos})

def detalle_articulo(request, slug):
    articulo = get_object_or_404(Articulo, slug=slug, publicado=True)
    return render(request, 'detalle_articulo.html', {'articulo': articulo})

def blog_detalle(request, articulo_id):
    articulo = Articulo.objects.get(id=articulo_id)
    return render(request, 'blog_detail.html', {'articulo': articulo})


def finalizar_compra_whatsapp(request):
    """Guarda el pedido web en una transaccion y abre WhatsApp de Arkadya."""
    carrito = request.session.get('carrito', {})

    if not carrito:
        return redirect('catalogo')

    if request.method != 'POST':
        return render(request, 'finalizar_compra.html', {'carrito': carrito})

    nombre = request.POST.get('nombre')
    telefono = request.POST.get('telefono')
    localidad = request.POST.get('localidad', '')
    metodo_pago = request.POST.get('metodo_pago', 'transferencia')
    metodo_entrega = request.POST.get('metodo_entrega', 'delivery')
    primer_item = list(carrito.values())[0]
    moneda = primer_item.get('moneda', 'PYG')

    try:
        with transaction.atomic():
            cliente = obtener_o_crear_cliente(nombre, telefono, localidad)
            total_pyg = Decimal('0')
            detalles = []

            for item in carrito.values():
                try:
                    producto = Producto.objects.select_for_update().get(id=item['id'])
                except Producto.DoesNotExist:
                    raise ValueError('Un producto del carrito ya no esta disponible.')

                cantidad = int(item['cantidad'])
                if cantidad < 1:
                    raise ValueError('La cantidad debe ser mayor a cero.')
                if not producto.hay_stock(cantidad):
                    raise ValueError(
                        f"{producto.nombre} (solicitado: {cantidad}, disponible: {producto.stock})"
                    )

                precio_unitario = producto.precio_pyg
                total_pyg += precio_unitario * cantidad
                detalles.append({
                    'producto': producto,
                    'cantidad': cantidad,
                    'precio_unitario': precio_unitario,
                })

            venta = Venta.objects.create(
                cliente=cliente,
                estado='pendiente',
                origen='web',
                moneda=moneda,
                subtotal=total_pyg,
                costo_envio=0,
                total=total_pyg,
                metodo_pago=metodo_pago,
                metodo_entrega=metodo_entrega,
                se_envio=False,
                facturado=False,
            )

            for detalle in detalles:
                DetalleVenta.objects.create(
                    venta=venta,
                    producto=detalle['producto'],
                    cantidad=detalle['cantidad'],
                    precio_unitario=detalle['precio_unitario'],
                    moneda='PYG',
                )

            cliente.cantidad_compras += 1
            cliente.save()
    except ValueError as exc:
        return render(request, 'finalizar_compra.html', {
            'carrito': carrito,
            'errores_stock': [str(exc)],
            'mensaje_error': 'No pudimos completar el pedido. Por favor, revisa el carrito.',
        })

    request.session['carrito'] = {}
    request.session.modified = True

    mensaje = "*ARKADYA COBRE - PEDIDO CONFIRMADO*\n\n"
    mensaje += f"*Numero de pedido:* {venta.nro_pedido}\n"
    mensaje += f"*Cliente:* {cliente.nombre}\n"
    mensaje += f"*Telefono:* {cliente.telefono}\n"
    mensaje += f"*Localidad:* {cliente.localidad}\n\n"
    mensaje += "*PRODUCTOS:*\n"

    for detalle in detalles:
        subtotal_detalle = detalle['precio_unitario'] * detalle['cantidad']
        mensaje += (
            f"- {detalle['cantidad']} x {detalle['producto'].nombre} = "
            f"PYG {subtotal_detalle:,.0f}\n"
        )

    mensaje += f"\n*TOTAL: PYG {total_pyg:,.0f}*\n"
    mensaje += f"*Metodo de pago:* {dict(Venta.METODO_PAGO).get(metodo_pago, metodo_pago)}\n"
    mensaje += f"*Metodo de entrega:* {dict(Venta.ENTREGA).get(metodo_entrega, metodo_entrega)}\n\n"
    mensaje += "Gracias por tu compra.\n"
    mensaje += "Nos pondremos en contacto para coordinar envio y pago.\n\n"
    mensaje += "WhatsApp: +595 991519823\n"
    mensaje += "Instagram: @arkadyacobre"

    import urllib.parse
    mensaje_codificado = urllib.parse.quote(mensaje)
    whatsapp_url = f"https://wa.me/595991519823?text={mensaje_codificado}"

    return redirect(whatsapp_url)

