from decimal import Decimal

from django.test import Client as TestClient
from django.test import TestCase

from productos.models import Producto
from ventas.models import Cliente, DetalleVenta, Venta


class CheckoutWebTests(TestCase):
    def setUp(self):
        self.client = TestClient()
        self.producto = Producto.objects.create(
            nombre='Vaso de prueba',
            descripcion='Producto de prueba',
            stock=4,
            stock_minimo=1,
            precio_pyg=Decimal('160000'),
            categoria='vasos',
            destacado=True,
        )

    def cargar_carrito(self, producto_id=None, cantidad=2, precio=1):
        session = self.client.session
        session['carrito'] = {
            str(producto_id or self.producto.id): {
                'id': str(producto_id or self.producto.id),
                'nombre': 'Nombre manipulado',
                'precio': precio,
                'cantidad': cantidad,
                'moneda': 'PYG',
            }
        }
        session.save()

    def post_checkout(self):
        return self.client.post('/finalizar-compra/', data={
            'nombre': 'Cliente Web',
            'telefono': '0981123456',
            'localidad': 'Asuncion',
            'metodo_pago': 'transferencia',
            'metodo_entrega': 'delivery',
        })

    def test_checkout_usa_precio_real_y_descuenta_stock(self):
        self.cargar_carrito(cantidad=2, precio=1)

        response = self.post_checkout()

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('https://wa.me/595991519823'))
        venta = Venta.objects.get()
        self.assertEqual(venta.subtotal, Decimal('320000'))
        self.assertEqual(venta.total, Decimal('320000'))
        detalle = DetalleVenta.objects.get(venta=venta)
        self.assertEqual(detalle.precio_unitario, Decimal('160000'))
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 2)
        self.assertEqual(Cliente.objects.get().cantidad_compras, 1)
        self.assertEqual(self.client.session.get('carrito'), {})

    def test_checkout_bloquea_stock_insuficiente(self):
        self.cargar_carrito(cantidad=5, precio=1)

        response = self.post_checkout()

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No pudimos completar el pedido')
        self.assertEqual(Venta.objects.count(), 0)
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 4)

    def test_checkout_maneja_producto_inexistente(self):
        self.cargar_carrito(producto_id=9999, cantidad=1, precio=1)

        response = self.post_checkout()

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ya no esta disponible')
        self.assertEqual(Venta.objects.count(), 0)
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 4)
