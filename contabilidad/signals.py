from django.db.models.signals import post_save
from django.dispatch import receiver
from ventas.models import Venta
from contabilidad.models import Ingreso

@receiver(post_save, sender=Venta)
def gestionar_stock_y_ingreso(sender, instance, created, **kwargs):
    """
    - Cuando una venta se completa, crea el ingreso contable.
    - Cuando una venta se cancela, restaura el stock.
    """
    # 1. Manejar ingreso contable si la venta está completada
    if instance.estado == 'completado':
        ingreso, creado = Ingreso.objects.get_or_create(
            venta=instance,
            defaults={
                'monto': instance.total,
                'moneda': instance.moneda,
                'descripcion': f"Venta #{instance.nro_pedido} - {instance.cliente.nombre}"
            }
        )
        if creado:
            print(f"✅ Ingreso creado para venta completada: {instance.nro_pedido}")
    else:
        # Si no está completada, eliminar ingreso (en caso de que existiera)
        Ingreso.objects.filter(venta=instance).delete()

    # 2. Si la venta se cancela (y no es una venta nueva), restaurar stock
    if not created and instance.estado == 'cancelado':
        # Usamos un atributo temporal para no restaurar múltiples veces
        if not hasattr(instance, '_stock_restaurado'):
            for detalle in instance.detalles.all():
                producto = detalle.producto
                producto.stock += detalle.cantidad
                producto.save()
                print(f"🔄 Stock restaurado: {producto.nombre} +{detalle.cantidad} (ahora: {producto.stock})")
            instance._stock_restaurado = True