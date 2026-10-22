En cada respuesta:

escribí entre cuatro y ocho oraciones,
usá al menos un ejemplo concreto de este TP: una falla, un test o un resultado que hayas obtenido.
Una respuesta correcta pero general, que se podría escribir sin haber hecho el TP, no obtiene el puntaje completo.

¿Cuántos tests unitarios, de integración y E2E tenés? ¿Por qué esa proporción?
¿Qué falla de pedidos.py no podía encontrarse con un test unitario de checkout.py? ¿Por qué?
¿Qué falla de api.py estaba en el paso de información entre dos partes del sistema? ¿Qué parte tendría que haberla resuelto?
¿Cuál de las fallas que encontraste habría sido la más cara de descubrir en producción? ¿Por qué?
¿Qué mide la cobertura, qué mide la mutación y qué mide la inyección de fallas? ¿En qué se diferencian?
Si una IA escribiera tus tests de integración y E2E, ¿qué le faltaría probar? ¿Cómo lo comprobarías?


## 1. ¿Cuántos tests unitarios, de integración y E2E tenés? ¿Por qué esa proporción?
Hay 46 funciones de tests unitarios, 12 de integración y 17 E2E. La base unitaria es grande porque esos tests son baratos y precisos: test_cantidad_diez_es_valida señala el < 10 exacto, y los bordes (5 prendas, el 30/11, los $60.000) piden muchos casos. Los de integración son pocos porque cada uno necesita una base SQLite real y prueba algo puntual de R10, como test_otra_conexion_ve_todos_los_items_del_pedido para el commit. Los E2E son más que los de integración porque la frontera HTTP recibe muchas formas de entrada; test_cuerpo_que_no_es_json_devuelve_400, por ejemplo, prueba cinco cuerpos rotos. Por eso la forma no es una pirámide perfecta.

## 2. ¿Qué falla de pedidos.py no podía encontrarse con un test unitario de checkout.py? ¿Por qué?
Es H-25, el commit que falta al final de guardar_pedido. calcular_total devuelve bien los importes, y un unitario solo ve ese diccionario porque nunca abre una base. Se ve únicamente con una segunda conexión: test_otra_conexion_ve_todos_los_items_del_pedido cuenta filas con contar(ruta, "items") desde otra conexión y, con tu pedidos.py original, obtiene 0 en vez de 

## 3. ¿Qué falla de api.py estaba en el paso de información entre dos partes del sistema? ¿Qué parte tendría que haberla resuelto?
Es H-35, la fecha. api.py recibe "fecha": "2026-11-30" como texto y se la pasa sin convertir a checkout, que espera un date. Al comparar estalla con '>' not supported between instances of 'str' and 'datetime.date' y el cliente recibe un 500. Seis casos E2E fallan con ese mensaje, incluido test_post_crea_un_pedido_y_responde_201, o sea el ejemplo de la especificación. Le tocaba resolverlo a api.py, que es la capa que habla en texto JSON: debía convertir AAAA-MM-DD a date o responder 400 FECHA_INVALIDA.

## 4. ¿Cuál de las fallas que encontraste habría sido la más cara de descubrir en producción? ¿Por qué?
La falla H-25, el commit que falta. El frontend recibe un 201 y muestra “pedido confirmado”, pero al cerrar la conexión la base queda con un pedido en $0 y sin ítems. No salta ningún error y nadie se entera hasta que la comisión revisa la base o un comprador reclama que pagó y no tiene pedido. Para entonces puede haber cientos de pedidos vacíos, sin forma de reconstruir qué compró cada uno. H-05 (el cupón DEBUG100) también es grave, pero se corrige con una línea y un cálculo de cuánto se regaló. H-25 destruye información que ya no se puede recuperar, y por eso la audité como crítica.

## 5. ¿Qué mide la cobertura, qué mide la mutación y qué mide la inyección de fallas? ¿En qué se diferencian?
La cobertura mide qué líneas se ejecutaron, no qué se verificó sobre ellas. La auditoría lo muestra con test_total_funciona, que ejecuta todo el camino pero solo comprueba que el resultado no sea None. La mutación cambia el código (por ejemplo > por >=) y mide si algún test lo nota: el puntaje de 58,6 % (17 mutantes muertos de 29) indica que 12 cambios pasaban inadvertidos, como el del borde de > 5 en H-14. La inyección de fallas rompe el entorno en lugar del código, por ejemplo un error de cálculo en medio de guardar_pedido o una conexión que falla, y mide si el sistema se comporta bien ante el problema. El test del zapato en el carrito, que debe dejar cero filas, es de este tipo. 
La cobertura mira si el código se ejecutó, la mutación mira si los tests están atentos al código, y la inyección de fallas mira si el sistema aguanta cuando algo sale mal.

## 6. Si una IA escribiera tus tests de integración y E2E, ¿qué le faltaría probar? ¿Cómo lo comprobarías?
Escribiría el camino feliz con valores cómodos, sin segunda conexión y sin datos hostiles. Se perdería H-25, y se perdería también la diferencia entre Decimal("24999.90") y Decimal(24999.9). Los archivos recortados muestran el mismo hueco: sin inyección SQL en integración, y sin FECHA_INVALIDA ni RUTA_INEXISTENTE en E2E. Lo comprobaría corriendo los tests contra el código con fallas conocidas y contra una referencia corregida. Con tus pedidos.py y api.py originales fallan 24 de 25 casos de integración y 45 de 45 E2E, y contra la referencia pasan 25/25 y 45/45. El único caso de integración que pasa con el original es remera en test_precio_unitario_es_decimal_exacto, porque 11999.50 es exacto en float. Ese caso no discrimina, y por eso están también buzo y campera.