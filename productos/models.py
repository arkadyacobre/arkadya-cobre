from django.db import models

class Producto(models.Model):

    orden = models.IntegerField(default=0, help_text="Número de orden (menor = más arriba)")
    
    CATEGORIAS = [
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
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    foto = models.ImageField(upload_to='productos/', blank=True, null=True, verbose_name="Imagen del producto")
    stock = models.IntegerField(default=0, help_text="Stock disponible")
    stock_minimo = models.IntegerField(default=5, help_text="Stock mínimo para alerta")
    precio_pyg = models.DecimalField(max_digits=12, decimal_places=0, default=0, help_text="Precio en Guaraníes")
    categoria = models.CharField(max_length=50, choices=CATEGORIAS, blank=True, null=True)
    destacado = models.BooleanField(default=False, help_text="Mostrar en la página principal")

    es_vertical = models.BooleanField(
    default=False,
    verbose_name="Imagen vertical (alta)",
    help_text="Marca esta casilla si la imagen es más alta que ancha (Ej: botellas, jarras)"
    )
    
    def __str__(self):
        return f"{self.nombre} (Stock: {self.stock})"
    
    def hay_stock(self, cantidad=1):
        return self.stock >= cantidad
    
    def descontar_stock(self, cantidad=1):
        if self.hay_stock(cantidad):
            self.stock -= cantidad
            self.save()
            return True
        return False
    
    def aumentar_stock(self, cantidad=1):
        self.stock += cantidad
        self.save()


def hay_stock(self, cantidad=1):
    return self.stock >= cantidad


class TasaCambio(models.Model):
    MONEDAS = [
        ('USD', 'Dólar Americano'),
        ('EUR', 'Euro'),
        ('ARS', 'Peso Argentino'),
        ('BRL', 'Real Brasileño'),
    ]
    
    moneda = models.CharField(max_length=3, choices=MONEDAS, unique=True)
    tasa = models.DecimalField(max_digits=12, decimal_places=2, help_text="Ej: 7500 = 1 USD = 7500 PYG")
    ultima_actualizacion = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"1 {self.moneda} = {self.tasa} PYG"


class Proveedor(models.Model):
    nombre = models.CharField(max_length=200)
    empresa = models.CharField(max_length=200)
    contacto = models.CharField(max_length=100)
    telefono = models.CharField(max_length=50)
    
    def __str__(self):
        return self.empresa



