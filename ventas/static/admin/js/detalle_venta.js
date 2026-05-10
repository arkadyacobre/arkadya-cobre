// Esperar a que el DOM cargue
document.addEventListener('DOMContentLoaded', function() {
    // Función para obtener el precio del producto via API
    async function obtenerPrecioProducto(productoId) {
        try {
            const response = await fetch(`/admin/api/producto-precio/${productoId}/`);
            const data = await response.json();
            return data.precio_pyg;
        } catch (error) {
            console.error('Error al obtener precio:', error);
            return 0;
        }
    }
    
    // Observar cambios en los selects de producto
    function setupProductoSelects() {
        const rows = document.querySelectorAll('.dynamic-detalleventa');
        
        rows.forEach(row => {
            const productoSelect = row.querySelector('select[name$="-producto"]');
            const precioInput = row.querySelector('input[name$="-precio_unitario"]');
            
            if (productoSelect && precioInput && !productoSelect.hasListener) {
                productoSelect.hasListener = true;
                
                productoSelect.addEventListener('change', async function() {
                    const productoId = this.value;
                    if (productoId) {
                        const precio = await obtenerPrecioProducto(productoId);
                        if (precio) {
                            precioInput.value = precio;
                            // Disparar evento para que Django reconozca el cambio
                            precioInput.dispatchEvent(new Event('change', { bubbles: true }));
                        }
                    }
                });
            }
        });
    }
    
    // Configurar para filas existentes y nuevas
    setupProductoSelects();
    
    // Observar cuando se agregan nuevas filas
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.addedNodes.length) {
                setupProductoSelects();
            }
        });
    });
    
    observer.observe(document.body, { childList: true, subtree: true });
});