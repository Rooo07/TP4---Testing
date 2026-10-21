# Sección 1 

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


# Sección 2

## checkout.py

## H-01 · Dinero en `float`

- **Ubicación:** checkout.py, líneas 29–33 (catálogo), 38–40 (cupones), 43–48 (envíos), 76 y 104 (acumuladores)
- **Categoría:** numéricos
- **Regla violada:** R7 y contrato §1 (todas las funciones devuelven `Decimal`)
- **Cómo la encontré:** lectura de la spec (R7 dice "nunca float") contra los literales del catálogo
- **Severidad:** alta — los errores binarios se acumulan en los totales y se propagan a la base y a la API


## H-02 · `round()` no hace redondeo comercial

- **Ubicación:** checkout.py, líneas 86, 132 y 187
- **Categoría:** numéricos
- **Regla violada:** R7 (el medio centavo redondea hacia arriba)
- **Cómo la encontré:** ejemplo de R7 en la spec, calculado a mano y en el intérprete
- **Severidad:** media — un centavo por compra, pero el importe guardado no coincide con el que la spec define


## H-03 · El precio lo puede poner el cliente

- **Ubicación:** checkout.py, línea 80 (`item.get("precio", CATALOGO[...])`)
- **Categoría:** seguridad
- **Regla violada:** R1 (el precio sale siempre del catálogo; un precio propio se ignora)
- **Cómo la encontré:** lectura del código (caja blanca): el `.get` con valor por defecto
- **Severidad:** crítica — permite comprar a cualquier precio


## H-04 · Productos inexistentes se saltean en silencio (`except:` desnudo)

- **Ubicación:** checkout.py, líneas 79–83; `validar_item` (51–64) no valida el producto
- **Categoría:** manejo de errores
- **Regla violada:** R1 (producto fuera del catálogo → `PRODUCTO_INEXISTENTE`) y §3 (el producto se valida primero)
- **Cómo la encontré:** linter (E722) y lectura del comentario "lo salteamos"
- **Severidad:** alta — el cliente cree que compró algo que nunca se cobra ni se entrega


## H-05 · Cupón de depuración `DEBUG100` en producción

- **Ubicación:** checkout.py, línea 40
- **Categoría:** seguridad
- **Regla violada:** R6 (EGRESADOS2026 y BIENVENIDA son los únicos dos cupones)
- **Cómo la encontré:** lectura del código: el `# TODO: sacar antes de producción` (y el linter marcó la línea por E501)
- **Severidad:** crítica — compras gratis para cualquiera


## H-06 · `validar_item` modifica el ítem que recibe

- **Ubicación:** checkout.py, línea 58 (`item["talle"] = item["talle"].upper()`)
- **Categoría:** estado y efectos laterales
- **Regla violada:** R4 (ninguna función modifica el carrito)
- **Cómo la encontré:** lectura del código (asignación sobre el parámetro)
- **Severidad:** media — corrompe el estado del cliente


## H-07 · El talle no ignora los espacios

- **Ubicación:** checkout.py, línea 58
- **Categoría:** strings y normalización
- **Regla violada:** R2 (`"  M "` es válido)
- **Cómo la encontré:** caja negra: el caso de R2 de `CASOS.md`
- **Severidad:** media — se rechazan compras válidas


## H-08 · Talle ausente o que no es texto revienta con otra excepción

- **Ubicación:** checkout.py, línea 58
- **Categoría:** validación de tipos
- **Regla violada:** R2 y §1 (ante datos inválidos, siempre `CheckoutError`)
- **Cómo la encontré:** lectura del código: `.upper()` sin chequear el tipo
- **Severidad:** media


## H-09 · Mensaje de talle inválido distinto al del contrato

- **Ubicación:** checkout.py, línea 61
- **Categoría:** contrato entre capas
- **Regla violada:** §7, ejemplo de error: `"Talle inválido: 'XXXL'"`
- **Cómo la encontré:** comparación con el ejemplo de la spec
- **Severidad:** baja


## H-10 · La cantidad 10 se rechaza

- **Ubicación:** checkout.py, línea 63 (`< 10`)
- **Categoría:** lógica y valores límite
- **Regla violada:** R3 (entre 1 y 10, ambos inclusive). El propio mensaje de error dice "entre 1 y 10".
- **Cómo la encontré:** valor límite de `CASOS.md`; el mutante `<` → `<=` sobrevivió a la suite de la IA
- **Severidad:** media


## H-11 · La cantidad no se valida como entero

- **Ubicación:** checkout.py, línea 63
- **Categoría:** validación de tipos
- **Regla violada:** R3 (cualquier valor no entero → `CANTIDAD_INVALIDA`)
- **Cómo la encontré:** caja negra (particiones de tipo de R3)
- **Severidad:** media — se pueden comprar fracciones de prenda


## H-12 · El carrito vacío se acepta

- **Ubicación:** checkout.py, líneas 67–86 (no hay ningún chequeo)
- **Categoría:** lógica y valores límite
- **Regla violada:** R4 (al menos un ítem → si no, `CARRITO_VACIO`) y §3 (es lo primero que se valida)
- **Cómo la encontré:** caja negra (partición "0 ítems"): no hay ninguna línea que lo controle
- **Severidad:** alta — se cobra y se guarda un pedido sin productos


## H-13 · La fecha por defecto se evalúa al importar el módulo

- **Ubicación:** checkout.py, líneas 89 y 161 (`fecha=date.today()`)
- **Categoría:** tiempo y fechas
- **Regla violada:** R6 (sin `fecha` se usa la del día de la llamada) y el contrato (`fecha: date | None = None`)
- **Cómo la encontré:** linter (B008)
- **Severidad:** alta — el cupón no vence nunca en un servidor que no se reinicia


## H-14 · Con 5 prendas no hay descuento por cantidad

- **Ubicación:** checkout.py, línea 107 (`> 5`)
- **Categoría:** lógica y valores límite
- **Regla violada:** R5 (5 o más). El docstring de la línea 92 dice "5 prendas o más" y el código hace otra cosa.
- **Cómo la encontré:** valor límite de `CASOS.md`; el mutante `>` → `>=` sobrevivió a la suite de la IA
- **Severidad:** media

## H-15 · Cupón vacío o de espacios es un error

- **Ubicación:** checkout.py, línea 111 (`if cupon != None`)
- **Categoría:** strings y normalización
- **Regla violada:** R6 (`None`, `""` o solo espacios equivalen a no usar cupón)
- **Cómo la encontré:** linter (E711) me llevó a la línea; el caso `""` de `CASOS.md` mostró la falla
- **Severidad:** media


## H-16 · El cupón distingue mayúsculas

- **Ubicación:** checkout.py, línea 112 (`cupon.strip()` sin `.upper()`)
- **Categoría:** strings y normalización
- **Regla violada:** R6 (no se distingue mayúscula de minúscula)
- **Cómo la encontré:** caja negra
- **Severidad:** media

## H-17 · EGRESADOS2026 vence un día antes

- **Ubicación:** checkout.py, línea 120 (`if not fecha < datos["vence"]`)
- **Categoría:** tiempo y fechas (valor límite)
- **Regla violada:** R6 (válido hasta el 30/11/2026 **inclusive**)
- **Cómo la encontré:** valor límite de `CASOS.md`; el mutante `<` → `<=` sobrevivió a la suite de la IA
- **Severidad:** alta — es el último día de la promoción, el de más compras


## H-18 · Cupón y descuento por cantidad se acumulan

- **Ubicación:** checkout.py, líneas 108, 122 y 130 (`descuento +=`)
- **Categoría:** lógica
- **Regla violada:** R6 (no se acumulan: se calculan los dos y se aplica el mayor)
- **Cómo la encontré:** lectura del código contra la regla
- **Severidad:** alta — descuento de más en cada compra grande con cupón


## H-19 · El descuento puede superar el subtotal

- **Ubicación:** checkout.py, línea 132 (no hay tope)
- **Categoría:** lógica
- **Regla violada:** R6 (el descuento nunca puede superar el subtotal)
- **Cómo la encontré:** combinando dos hallazgos anteriores en el intérprete
- **Severidad:** alta — un total negativo es un reembolso


## H-20 · Cupón o zona que no son texto revientan con otra excepción

- **Ubicación:** checkout.py, líneas 112 y 147 (`.strip()` sin chequear el tipo)
- **Categoría:** validación de tipos
- **Regla violada:** §1 (nunca otro tipo de excepción que `CheckoutError`)
- **Cómo la encontré:** lectura del código
- **Severidad:** media


## H-21 · `ENVIOS.keys().join(...)` no existe

- **Ubicación:** checkout.py, línea 152
- **Categoría:** alucinación
- **Regla violada:** R8 (zona que no existe → `ZONA_INVALIDA`)
- **Cómo la encontré:** caja negra (zona `"LUNA"`); la suite de la IA nunca ejecutó esa rama
- **Severidad:** alta — ningún error de zona se informa bien; en la API es siempre 500


## H-22 · El envío gratis se mide sobre el subtotal sin descuento

- **Ubicación:** checkout.py, línea 180 (`calcular_envio(subtotal, zona)`)
- **Categoría:** lógica
- **Regla violada:** R8 (gratis si el subtotal **ya con el descuento aplicado** es ≥ 60.000)
- **Cómo la encontré:** lectura del código contra la regla (el docstring de `calcular_envio` también lo describe mal)
- **Severidad:** alta — se pierde el envío en cada compra cerca de 60.000 con descuento


## H-23 · `import json` sin uso

- **Ubicación:** checkout.py, línea 15
- **Categoría:** code smell
- **Regla violada:** —
- **Cómo la encontré:** linter (F401)
- **Severidad:** baja

---

## pedidos.py

## H-24 · El pedido se confirma antes de calcular los importes

- **Ubicación:** pedidos.py, líneas 68–80 (`INSERT` + `con.commit()` y recién después `calcular_total`)
- **Categoría:** transacciones y persistencia
- **Regla violada:** R10 (si `calcular_total` lanza, no queda nada guardado)
- **Cómo la encontré:** lectura del código (el orden de los pasos 1 y 2)
- **Severidad:** alta — pedidos fantasma de $ 0 en la base de la comisión


## H-25 · Falta el commit final

- **Ubicación:** pedidos.py, líneas 83–103 (el `UPDATE` y los `INSERT` de ítems nunca se confirman)
- **Categoría:** transacciones y persistencia
- **Regla violada:** R10 (al terminar, cualquier otra conexión ve el pedido completo)
- **Cómo la encontré:** lectura del código, buscando cada `commit`
- **Severidad:** crítica — el frontend muestra "pedido confirmado" y el pedido no existe

## H-26 · Los importes se guardan como `REAL`

- **Ubicación:** pedidos.py, líneas 25–28 y 36 (esquema), 86–89 y 100 (`float(...)`)
- **Categoría:** transacciones y persistencia (datos que cambian al guardarse)
- **Regla violada:** R10 (montos idénticos, sin pérdida)
- **Cómo la encontré:** lectura del esquema
- **Severidad:** alta — la base no guarda lo que se cobró


## H-27 · `Decimal(float)` al leer

- **Ubicación:** pedidos.py, líneas 121–124 y 130
- **Categoría:** contrato entre capas
- **Regla violada:** R10 (montos idénticos a los que calculó checkout)
- **Cómo la encontré:** test de integración que compara contra `calcular_total`
- **Severidad:** alta


## H-28 · `precio_unitario` es el que manda el cliente

- **Ubicación:** pedidos.py, línea 96
- **Categoría:** seguridad
- **Regla violada:** R10 (`precio_unitario` es el del catálogo)
- **Cómo la encontré:** lectura del código (la misma línea que H-03, copiada)
- **Severidad:** alta — registros de venta falsos


## H-29 · Inyección SQL en `pedidos_de`

- **Ubicación:** pedidos.py, línea 141 (f-string con el email)
- **Categoría:** seguridad
- **Regla violada:** R10 (ningún valor del email puede alterar la consulta)
- **Cómo la encontré:** lectura del código (la única consulta armada con f-string)
- **Severidad:** crítica — expone datos personales de todos los compradores


## H-30 · La clave foránea está declarada pero desactivada

- **Ubicación:** pedidos.py, línea 32 (`REFERENCES pedidos(id)`) y `conectar` (41–45)
- **Categoría:** code smell
- **Regla violada:** —
- **Cómo la encontré:** lectura del esquema
- **Severidad:** baja

---

## api.py

## H-31 · Un error de negocio devuelve 500

- **Ubicación:** api.py, líneas 73–74 (`except Exception` → 500)
- **Categoría:** manejo de errores
- **Regla violada:** R11 (`CheckoutError` → 422 con su `code`; un error nunca devuelve 500)
- **Cómo la encontré:** lectura del código (un solo `except` para todo)
- **Severidad:** alta


## H-32 · Formato de error incorrecto y fuga de detalles internos

- **Ubicación:** api.py, líneas 74 y 89 (`{"error": str(e)}`)
- **Categoría:** manejo de errores (y seguridad)
- **Regla violada:** R11 (todos los errores son `{"error": {"code": …, "message": …}}`)
- **Cómo la encontré:** comparación con la tabla de errores de la spec
- **Severidad:** media


## H-33 · Cuerpo que no es JSON devuelve 500

- **Ubicación:** api.py, líneas 51–52
- **Categoría:** manejo de errores
- **Regla violada:** R11 (`400 JSON_INVALIDO`)
- **Cómo la encontré:** caja negra (tabla de errores de R11)
- **Severidad:** media


## H-34 · Faltan datos o tienen otro tipo: 500 (o 422)

- **Ubicación:** api.py, líneas 57–59 (`datos["email"]`, etc.)
- **Categoría:** validación de tipos
- **Regla violada:** R11 (`400 DATOS_INCOMPLETOS`)
- **Cómo la encontré:** caja negra
- **Severidad:** media


## H-35 · La fecha llega a checkout como texto

- **Ubicación:** api.py, línea 61 (`datos.get("fecha")`)
- **Categoría:** contrato entre capas
- **Regla violada:** R11 (la fecha viaja como `AAAA-MM-DD`; si no, `400 FECHA_INVALIDA`) y contrato de checkout (`fecha: date`)
- **Cómo la encontré:** test E2E del flujo con cupón y fecha
- **Severidad:** alta


## H-36 · Los montos viajan como número JSON

- **Ubicación:** api.py, línea 37 (`json.dumps(..., default=float)`)
- **Categoría:** contrato entre capas
- **Regla violada:** R11 (los montos viajan siempre como texto) y R7
- **Cómo la encontré:** lectura del código (`default=float` convierte cada `Decimal`)
- **Severidad:** alta


## H-37 · Pedido inexistente responde 200 con `null`

- **Ubicación:** api.py, líneas 85–87
- **Categoría:** manejo de errores
- **Regla violada:** R11 (`404 PEDIDO_INEXISTENTE`)
- **Cómo la encontré:** caja negra
- **Severidad:** media


## H-38 · Un id gigante revienta SQLite

- **Ubicación:** api.py, línea 85 (`int(...)` sin límite)
- **Categoría:** validación de tipos
- **Regla violada:** R11 (un error nunca devuelve 500)
- **Cómo la encontré:** valor límite del id (más allá de `2^63 − 1`)
- **Severidad:** baja


## H-39 · La conexión no se cierra si hay un error

- **Ubicación:** api.py, líneas 54–64 y 84–86 (`con.close()` solo en el camino feliz)
- **Categoría:** code smell
- **Regla violada:** —
- **Cómo la encontré:** lectura del código
- **Severidad:** baja


## H-40 · `\d` en la ruta acepta dígitos que no son ASCII

- **Ubicación:** api.py, línea 27
- **Categoría:** code smell
- **Regla violada:** —
- **Cómo la encontré:** lectura del código
- **Severidad:** baja


---

## Resumen ordenado por severidad

| Severidad | Hallazgo | Módulo | Categoría |
|---|---|---|---|
| Crítica | H-03 Precio del cliente | checkout | seguridad |
| Crítica | H-05 Cupón DEBUG100 | checkout | seguridad |
| Crítica | H-25 Falta el commit final | pedidos | transacciones |
| Crítica | H-29 Inyección SQL | pedidos | seguridad |
| Alta | H-01 Dinero en float | checkout | numéricos |
| Alta | H-04 Productos inexistentes salteados | checkout | manejo de errores |
| Alta | H-12 Carrito vacío aceptado | checkout | lógica |
| Alta | H-13 Fecha por defecto al importar | checkout | tiempo y fechas |
| Alta | H-17 Cupón vence un día antes | checkout | tiempo y fechas |
| Alta | H-18 Descuentos acumulados | checkout | lógica |
| Alta | H-19 Descuento mayor al subtotal | checkout | lógica |
| Alta | H-21 `ENVIOS.keys().join` | checkout | alucinación |
| Alta | H-22 Envío sobre subtotal sin descuento | checkout | lógica |
| Alta | H-24 Pedido confirmado antes de calcular | pedidos | transacciones |
| Alta | H-26 Importes como REAL | pedidos | transacciones |
| Alta | H-27 `Decimal(float)` al leer | pedidos | contrato entre capas |
| Alta | H-28 `precio_unitario` del cliente | pedidos | seguridad |
| Alta | H-31 CheckoutError → 500 | api | manejo de errores |
| Alta | H-35 Fecha como texto | api | contrato entre capas |
| Alta | H-36 Montos como número JSON | api | contrato entre capas |
| Media | H-02 Redondeo no comercial | checkout | numéricos |
| Media | H-06 Se modifica el ítem | checkout | estado |
| Media | H-07 Talle con espacios | checkout | strings |
| Media | H-08 Talle de otro tipo | checkout | validación de tipos |
| Media | H-10 Cantidad 10 rechazada | checkout | lógica |
| Media | H-11 Cantidad no entera | checkout | validación de tipos |
| Media | H-14 5 prendas sin descuento | checkout | lógica |
| Media | H-15 Cupón vacío es error | checkout | strings |
| Media | H-16 Cupón distingue mayúsculas | checkout | strings |
| Media | H-20 Cupón/zona de otro tipo | checkout | validación de tipos |
| Media | H-32 Formato de error y fuga | api | manejo de errores |
| Media | H-33 JSON inválido → 500 | api | manejo de errores |
| Media | H-34 Datos incompletos → 500 | api | validación de tipos |
| Media | H-37 Pedido inexistente → 200 | api | manejo de errores |
| Baja | H-09 Mensaje de talle | checkout | contrato entre capas |
| Baja | H-23 `import json` sin uso | checkout | code smell |
| Baja | H-30 Foreign key desactivada | pedidos | code smell |
| Baja | H-38 Id gigante → 500 | api | validación de tipos |
| Baja | H-39 Conexión sin cerrar | api | code smell |
| Baja | H-40 `\d` Unicode | api | code smell |
