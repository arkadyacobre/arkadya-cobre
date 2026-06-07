from django.core.exceptions import ValidationError
from django.db import models, transaction
from productos.models import Producto  # ← Agregar esta línea
from django.core.validators import MinValueValidator
from django.utils import timezone
import re

# ==========================================
# FUNCIÓN PARA NORMALIZAR TELÉFONOS
# ==========================================

def normalizar_telefono(telefono):
    """Convierte cualquier formato de teléfono a formato estándar +595XXXXXXXXX"""
    solo_numeros = re.sub(r'\D', '', telefono)
    
    if solo_numeros.startswith('0'):
        solo_numeros = solo_numeros[1:]
    
    if len(solo_numeros) == 9:
        return f"+595{solo_numeros}"
    elif len(solo_numeros) == 12:
        return f"+{solo_numeros}"
    elif len(solo_numeros) == 13:
        return f"+{solo_numeros}"
    else:
        return f"+595{solo_numeros[-9:]}"


# ==========================================
# FUNCIÓN PARA OBTENER O CREAR CLIENTE
# ==========================================

def obtener_o_crear_cliente(nombre_completo, telefono, localidad=""):
    telefono_normalizado = normalizar_telefono(telefono)
    cliente, creado = Cliente.objects.get_or_create(
        telefono=telefono_normalizado,
        defaults={'nombre': nombre_completo, 'localidad': localidad}
    )
    if not creado and cliente.nombre != nombre_completo:
        cliente.nombre = nombre_completo
        cliente.save()
    return cliente


# ==========================================
# MODELO CLIENTE
# ==========================================

class Cliente(models.Model):
    nombre = models.CharField(max_length=200)
    telefono = models.CharField(max_length=50, unique=True)
    localidad = models.CharField(max_length=200)
    instagram = models.CharField(max_length=100, blank=True)
    como_nos_conocio = models.CharField(max_length=200, blank=True)
    cantidad_compras = models.IntegerField(default=0)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        self.telefono = normalizar_telefono(self.telefono)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.nombre} ({self.telefono})"

# ==========================================
# MODELO VENTA UNIFICADO
# ==========================================

class Venta(models.Model):
    ESTADOS = [
        ('pendiente', '🟡 Pendiente (esperando pago)'),
        ('pagado', '🔵 Pagado (preparando envío)'),
        ('enviado', '🟣 Enviado (en camino)'),
        ('completado', '✅ Completado (entregado)'),
        ('cancelado', '❌ Cancelado'),
    ]
    
    ORIGENES = [
        ('web', '🌐 Web'),
        ('instagram', '📷 Instagram'),
        ('whatsapp', '💬 WhatsApp'),
        ('presencial', '🏪 Presencial'),
    ]
    
    MONEDAS = [
        ('PYG', 'Guaraníes'),
        ('USD', 'Dólares'),
        ('EUR', 'Euros'),
        ('ARS', 'Pesos Argentinos'),
        ('BRL', 'Reales Brasileños'),
    ]
    
    METODO_PAGO = [
        ('efectivo', 'Efectivo'),
        ('transferencia', 'Transferencia'),
        ('contra_entrega', 'Contra entrega'),
    ]
    
    ENTREGA = [
        ('retiro', 'Retiro en persona'),
        ('delivery', 'Delivery'),
        ('correo', 'Envío por correo'),
    ]
    
    # Relaciones
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='ventas')
    
    # Identificación
    nro_pedido = models.CharField(max_length=20, unique=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    origen = models.CharField(max_length=20, choices=ORIGENES, default='web')
    
    # Fechas
    fecha_pedido = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    # Productos (relación muchos a muchos)
    productos = models.ManyToManyField(Producto, through='DetalleVenta')
    
    # Montos
    moneda = models.CharField(max_length=3, choices=MONEDAS, default='PYG')
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    costo_envio = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Datos de envío y facturación
    metodo_pago = models.CharField(max_length=20, choices=METODO_PAGO, blank=True)
    metodo_entrega = models.CharField(max_length=20, choices=ENTREGA, blank=True)
    empresa_transporte = models.CharField(max_length=100, blank=True)
    se_envio = models.BooleanField(default=False)
    facturado = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.nro_pedido} - {self.cliente.nombre} - {self.get_estado_display()}"
    
    def save(self, *args, **kwargs):
        if not self.nro_pedido:
            # Generar nro de pedido: ARK-2026-0001
            año = timezone.now().year
            ultimo = Venta.objects.filter(nro_pedido__startswith=f"ARK-{año}-").count()
            self.nro_pedido = f"ARK-{año}-{ultimo + 1:04d}"
        super().save(*args, **kwargs)
    
    def actualizar_total(self):
        """Recalcula el total sumando los detalles"""
        total = sum(d.subtotal() for d in self.detalles.all())
        self.subtotal = total
        self.total = total + self.costo_envio
        self.save()
    
    def completar_venta(self):
        """Marca la venta como completada y crea ingreso contable"""
        if self.estado == 'pagado':
            self.estado = 'completado'
            self.save()
            # Aquí luego crearemos el ingreso contable
            return True
        return False
    
    def cancelar_venta(self):
        """Cancela la venta. La senal de Venta restaura el stock una sola vez."""
        if self.estado in ['pendiente', 'pagado']:
            self.estado = 'cancelado'
            self.save()
            return True
        return False
    
    # En ventas/models.py, dentro de la clase Venta agregar:
    def total_formateado(self):
        return f"{self.total:,.0f}".replace(',', '.')
    total_formateado.short_description = 'Total'

    def enviar_notificacion_whatsapp(self):
        """Envía notificación por WhatsApp según el estado del pedido"""
        import urllib.parse
        
        # Obtener número de teléfono del cliente (formato internacional)
        telefono = self.cliente.telefono.replace('+', '')
        
        # Plantillas según estado
        if self.estado == 'pagado':
            mensaje = f"""🏺 *ARKADYA COBRE - PAGO CONFIRMADO* 🏺

            📋 *Pedido:* {self.nro_pedido}
            👤 *Cliente:* {self.cliente.nombre}

            ✅ ¡Tu pago ha sido confirmado!

            📦 Tu pedido está siendo preparado para envío.
            Te notificaremos cuando esté en camino.

            📍 Asunción, Paraguay
            💬 ¿Dudas? Respondé este mensaje"""
        
        elif self.estado == 'enviado':
            mensaje = f"""🏺 *ARKADYA COBRE - PEDIDO EN CAMINO* 🏺

            📋 *Pedido:* {self.nro_pedido}
            👤 *Cliente:* {self.cliente.nombre}

            🚚 ¡Tu pedido está en camino!

            📍 Llegará en las próximas 24-48 horas.

            💬 Gracias por confiar en Arkadya Cobre"""
        
        elif self.estado == 'completado':
            mensaje = f"""🏺 *ARKADYA COBRE - PEDIDO COMPLETADO* 🏺

            📋 *Pedido:* {self.nro_pedido}
            👤 *Cliente:* {self.cliente.nombre}

            ✅ ¡Tu pedido ha sido entregado!

            📸 Etiquétanos en Instagram @arkadyacobre
            🫶 Gracias por tu compra. ¡Vuelve pronto!"""
        
        elif self.estado == 'cancelado':
            mensaje = f"""🏺 *ARKADYA COBRE - PEDIDO CANCELADO* 🏺

            📋 *Pedido:* {self.nro_pedido}
            👤 *Cliente:* {self.cliente.nombre}

            ❌ Tu pedido ha sido cancelado.

            💬 Si tienes dudas, respondé este mensaje."""
        
        else:
            # Pendiente - no notificar por ahora
            return
        
        # Codificar y enviar
        mensaje_codificado = urllib.parse.quote(mensaje)
        whatsapp_url = f"https://wa.me/{telefono}?text={mensaje_codificado}"
        
        # En producción, podrías usar una API como Twilio
        # Por ahora, retornamos la URL para pruebas
        return whatsapp_url

# ==========================================
# MODELO DETALLE VENTA
# ==========================================

class DetalleVenta(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)  # ← Usa Producto de productos
    cantidad = models.IntegerField(validators=[MinValueValidator(1)])
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    moneda = models.CharField(max_length=3, choices=Venta.MONEDAS, default='PYG')
    
    def subtotal(self):
        return self.precio_unitario * self.cantidad
    
    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre} = {self.subtotal()} {self.moneda}"
    
    def save(self, *args, **kwargs):
        with transaction.atomic():
            if self.pk:
                anterior = DetalleVenta.objects.select_for_update().get(pk=self.pk)
                if anterior.producto_id != self.producto_id:
                    if self.venta.estado != 'cancelado':
                        anterior.producto.aumentar_stock(anterior.cantidad)
                        if not self.producto.descontar_stock(self.cantidad):
                            raise ValidationError(f"No hay suficiente stock para {self.producto.nombre}.")
                else:
                    diferencia = self.cantidad - anterior.cantidad
                    if self.venta.estado != 'cancelado':
                        if diferencia > 0 and not self.producto.descontar_stock(diferencia):
                            raise ValidationError(f"No hay suficiente stock para {self.producto.nombre}.")
                        if diferencia < 0:
                            self.producto.aumentar_stock(abs(diferencia))
            elif self.venta.estado != 'cancelado':
                if not self.producto.descontar_stock(self.cantidad):
                    raise ValidationError(f"No hay suficiente stock para {self.producto.nombre}.")

            super().save(*args, **kwargs)
            self.venta.actualizar_total()
    
    def delete(self, *args, **kwargs):
        venta = self.venta
        if venta.estado != 'cancelado':
            self.producto.aumentar_stock(self.cantidad)
        super().delete(*args, **kwargs)
        venta.actualizar_total()
    

