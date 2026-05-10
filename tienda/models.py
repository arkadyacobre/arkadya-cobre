from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.core.validators import validate_image_file_extension

class Articulo(models.Model):
    titulo = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    contenido = models.TextField()
    fecha_publicacion = models.DateTimeField(auto_now_add=True)
    imagen = models.ImageField(upload_to='blog/', blank=True, null=True, verbose_name="Imagen destacada")
    imagenes_extra = models.TextField(default='[]', blank=True, help_text='Lista de rutas en formato JSON (ej: ["/media/blog/img1.jpg", "/media/blog/img2.jpg"])')
    publicado = models.BooleanField(default=True, help_text="Mostrar en el blog")
    orden = models.IntegerField(default=0, help_text="Número para ordenar (menor primero)")

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.titulo)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.titulo

    def get_absolute_url(self):
        return reverse('detalle_articulo', args=[self.slug])