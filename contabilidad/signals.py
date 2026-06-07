from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from contabilidad.models import Ingreso
from ventas.models import Venta


@receiver(pre_save, sender=Venta)
def guardar_estado_anterior(sender, instance, **kwargs):
    if not instance.pk:
        instance._estado_anterior = None
        return

    instance._estado_anterior = (
        Venta.objects
        .filter(pk=instance.pk)
        .values_list('estado', flat=True)
        .first()
    )


@receiver(post_save, sender=Venta)
def gestionar_stock_y_ingreso(sender, instance, created, **kwargs):
    """
    Crea/elimina ingresos contables segun el estado y restaura stock solo
    cuando una venta cambia por primera vez a cancelada.
    """
    if instance.estado == 'completado':
        Ingreso.objects.get_or_create(
            venta=instance,
            defaults={
                'monto': instance.total,
                'moneda': instance.moneda,
                'descripcion': f"Venta #{instance.nro_pedido} - {instance.cliente.nombre}",
            },
        )
    else:
        Ingreso.objects.filter(venta=instance).delete()

    estado_anterior = getattr(instance, '_estado_anterior', None)
    if not created and estado_anterior != 'cancelado' and instance.estado == 'cancelado':
        for detalle in instance.detalles.select_related('producto'):
            detalle.producto.aumentar_stock(detalle.cantidad)
