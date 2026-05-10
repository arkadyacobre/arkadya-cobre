from django.shortcuts import render
from django.http import JsonResponse
from .models import Producto

def api_producto_precio(request, producto_id):
    """API para obtener el precio de un producto por ID"""
    try:
        producto = Producto.objects.get(id=producto_id)
        return JsonResponse({
            'precio_pyg': float(producto.precio_pyg),
            'nombre': producto.nombre
        })
    except Producto.DoesNotExist:
        return JsonResponse({'error': 'Producto no encontrado'}, status=404)
# Create your views here.

