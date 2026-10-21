## Test por test

### 1. test_subtotal — Tautológico
Compara el subtotal con el precio del propio catálogo multiplicado por la cantidad, por lo que no detecta precios mal cargados ni el uso incorrecto de float.

### 2. test_total_funciona — Inútil
Solo comprueba que el resultado no sea None, sin verificar que el total, los descuentos o el envío sean correctos.

### 3. test_total_positivo — Débil
Verifica que el total sea mayor que cero, pero acepta cualquier importe positivo aunque esté mal calculado.

### 4. test_cupon_egresados — Débil
Comprueba el descuento del 15 % en una fecha válida, pero no verifica el vencimiento, la normalización del cupón, la acumulación de descuentos ni el tipo numérico.

### 5. test_envio_caba — Útil
Verifica que un subtotal de $10.000 para CABA genere un envío de $2.500, según el valor esperado de la especificación, aunque no cubre otros escenarios.

### 6. test_descuento_por_cantidad — Débil
Comprueba el descuento para seis prendas, pero no detecta el error en el límite de cinco unidades (> 5 en lugar de >= 5).

### 7. test_talle_valido — Débil 
Solo comprueba indirectamente que el talle "M" no provoque una excepción y, al no tener assert, no verifica el resultado ni el comportamiento de la función.

### 8. test_no_explota_con_varios_productos — Inútil
El bloque try/except Exception: pass oculta cualquier error, incluso los errores de aserción, por lo que no verifica el comportamiento esperado.


## Puntaje
Mutantes generados : 29

Muertos            : 17

Sobrevivientes     : 12

Puntaje de mutación: 58.6%


## ¿Por qué no entrega fallas?
La cobertura de líneas solo dice qué líneas se ejecutaron, no qué se verificó sobre ellas. Los tests de la IA recorren el camino feliz con valores cómodos, lejos de todos los bordes (6 prendas, subtotal 10.000, fecha 01/10), y casi no tienen oráculo: dos no pueden fallar, uno compara contra el propio código y otro solo pide > 0. Además, muchas fallas no están en una línea que se pueda "cubrir": son código que falta (no se valida el carrito vacío, no se normaliza el cupón, no hay tope de descuento) o están en ramas de error que nadie ejecuta (la rama con ENVIOS.keys().join nunca corrió, por eso nadie vio que explota). Y las fallas de tipo de dato (float en vez de Decimal) son invisibles si el valor esperado también se calcula en float. Una línea ejecutada sin un assert fuerte sobre su efecto no aporta evidencia.