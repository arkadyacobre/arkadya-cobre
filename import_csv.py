import csv
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'arkadya_system.settings')
django.setup()

from ventas.models import Cliente

def importar_clientes(archivo_csv):
    with open(archivo_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Verifica si el cliente ya existe (por ID o teléfono)
            cliente, creado = Cliente.objects.get_or_create(
                telefono=row.get('Teléfono', ''),
                defaults={
                    'nombre': row.get('Nombre', ''),
                    'localidad': row.get('Localidad', ''),
                    'cantidad_compras': int(row.get('Cantidad Compras', 0)) if row.get('Cantidad Compras') else 0
                }
            )
            if not creado:
                print(f"Cliente ya existía: {cliente.nombre}")
            else:
                print(f"Cliente importado: {cliente.nombre}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Uso: python importar_csv.py archivo.csv")
    else:
        importar_clientes(sys.argv[1])