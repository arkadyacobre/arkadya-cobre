from django.db import models
from ventas.models import Venta

class Ingreso(models.Model):
    venta = models.OneToOneField(Venta, on_delete=models.CASCADE, null=True, blank=True, related_name='ingreso')
    fecha = models.DateTimeField(auto_now_add=True)
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    moneda = models.CharField(max_length=3, default='PYG')
    descripcion = models.CharField(max_length=200, blank=True)
    
    def __str__(self):
        if self.venta:
            return f"Ingreso por Venta #{self.venta.id} - {self.monto} {self.moneda}"
        return f"Ingreso manual - {self.monto} {self.moneda}"
    
    class Meta:
        ordering = ['-fecha']
        verbose_name = "Ingreso"
        verbose_name_plural = "Ingresos"

class Gasto(models.Model):
    TIPOS = [
        ('insumo', 'Compra de insumos (cobre, materiales)'),
        ('envio', 'Gastos de envío'),
        ('comision', 'Comisiones (Payoneer, Creala)'),
        ('fijo', 'Gasto fijo (alquiler, internet, luz)'),
        ('imprevisto', 'Gasto imprevisto'),
        ('otro', 'Otro'),
    ]
    
    fecha = models.DateTimeField(auto_now_add=True)
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    moneda = models.CharField(max_length=3, default='PYG')
    tipo = models.CharField(max_length=20, choices=TIPOS)
    descripcion = models.CharField(max_length=200)
    comprobante = models.FileField(upload_to='comprobantes/', blank=True, null=True)
    
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.monto} {self.moneda} - {self.fecha.strftime('%d/%m/%Y')}"
    
    class Meta:
        ordering = ['-fecha']
        verbose_name = "Gasto"
        verbose_name_plural = "Gastos"

class CostoFijo(models.Model):
    nombre = models.CharField(max_length=200)
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    moneda = models.CharField(max_length=3, default='PYG')
    periodo = models.CharField(max_length=50, help_text="Ej: mensual, trimestral, anual")
    fecha_inicio = models.DateField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.nombre} - {self.monto} {self.moneda} ({self.periodo})"
    
    class Meta:
        verbose_name = "Costo Fijo"
        verbose_name_plural = "Costos Fijos"
