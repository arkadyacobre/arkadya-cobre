import json
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import Client as TestClient
from django.test import TestCase, override_settings

from productos.models import Producto
from ventas.models import Cliente, DetalleVenta, Venta


class StockVentaTests(TestCase):
    def setUp(self):
        self.producto = Producto.objects.create(
            nombre='Anillo de prueba',
            descripcion='Producto de prueba',
            stock=5,
            stock_minimo=1,
            precio_pyg=Decimal('50000'),
            categoria='anillos',
            destacado=True,
        )
        self.cliente = Cliente.objects.create(
            nombre='Cliente Prueba',
            telefono='0981123456',
            localidad='Asuncion',
        )
        self.venta = Venta.objects.create(cliente=self.cliente, estado='pendiente')

    def test_detalle_descuenta_stock_al_crear(self):
        DetalleVenta.objects.create(
            venta=self.venta,
            producto=self.producto,
            cantidad=2,
            precio_unitario=self.producto.precio_pyg,
        )

        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 3)

    def test_no_permite_detalle_sin_stock_suficiente(self):
        with self.assertRaises(ValidationError):
            DetalleVenta.objects.create(
                venta=self.venta,
                producto=self.producto,
                cantidad=6,
                precio_unitario=self.producto.precio_pyg,
            )

        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 5)

    def test_cancelar_venta_restaura_stock_una_sola_vez(self):
        DetalleVenta.objects.create(
            venta=self.venta,
            producto=self.producto,
            cantidad=2,
            precio_unitario=self.producto.precio_pyg,
        )

        self.venta.cancelar_venta()
        self.venta.save()

        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 5)


@override_settings(TOKEN_VENTA_RAPIDA='token-test')
class VentaRapidaApiTests(TestCase):
    def setUp(self):
        self.client = TestClient()
        self.producto = Producto.objects.create(
            nombre='Pulsera de prueba',
            descripcion='Producto de prueba',
            stock=3,
            stock_minimo=1,
            precio_pyg=Decimal('70000'),
            categoria='pulseras',
            destacado=True,
        )

    def test_venta_rapida_valida_stock(self):
        response = self.client.post(
            '/venta-rapida/api/guardar-venta/?token=token-test',
            data=json.dumps({
                'cliente_nombre': 'Cliente API',
                'cliente_telefono': '0981765432',
                'cliente_localidad': 'Asuncion',
                'productos': [{
                    'producto_id': self.producto.id,
                    'cantidad': 4,
                    'precio_unitario': 1,
                    'producto_nombre': 'Pulsera de prueba',
                }],
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 3)

    def test_venta_rapida_usa_precio_real_del_producto(self):
        response = self.client.post(
            '/venta-rapida/api/guardar-venta/?token=token-test',
            data=json.dumps({
                'cliente_nombre': 'Cliente API',
                'cliente_telefono': '0981765432',
                'cliente_localidad': 'Asuncion',
                'productos': [{
                    'producto_id': self.producto.id,
                    'cantidad': 2,
                    'precio_unitario': 1,
                    'producto_nombre': 'Pulsera de prueba',
                }],
                'costo_envio': 10000,
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        venta = Venta.objects.get()
        self.assertEqual(venta.subtotal, Decimal('140000'))
        self.assertEqual(venta.total, Decimal('150000'))
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 1)
