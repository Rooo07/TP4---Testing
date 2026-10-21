
## R1 — Catálogo y precios

| Partición | Límites / valores | Caso | Esperado | Nivel |
|---|---|---|---|---|
| Producto del catálogo | los 3 nombres | `calcular_subtotal([item("buzo","M",1)])` | `Decimal("24999.90")` | U |
| | | `calcular_subtotal([item("remera","M",1)])` | `Decimal("11999.50")` | U |
| | | `calcular_subtotal([item("campera","M",1)])` | `Decimal("47999.99")` | U |
| Nombre con otra capitalización | `"Buzo"`, `"BUZO"` | `validar_item(item("Buzo","M",1))` | `err(PRODUCTO_INEXISTENTE)` | U |
| Nombre con espacios | `" buzo"` | `validar_item(item(" buzo","M",1))` | `err(PRODUCTO_INEXISTENTE)` | U |
| Producto inexistente | `"gorra"`, `""` | `validar_item(item("gorra","M",1))` | `err(PRODUCTO_INEXISTENTE)` | U |
| Producto de otro tipo | `None`, `7`, `["buzo"]` | `validar_item(item(None,"M",1))` | `err(PRODUCTO_INEXISTENTE)` | U |
| Ítem sin clave producto / no dict | `{"talle":"M","cantidad":1}`, `None` | `validar_item(None)` | `err(PRODUCTO_INEXISTENTE)` | U |
| Ítem trae precio propio | `precio=1` | `calcular_subtotal([item("campera","M",1) + precio=1])` | `Decimal("47999.99")` | U |
| Precio propio no llega a la base | `precio=1` | `guardar_pedido(...)` → `precio_unitario` | `Decimal("47999.99")` | I |
| Producto inexistente entre válidos | 2º ítem malo | `calcular_subtotal([item("buzo",...), item("gorra",...)])` | `err(PRODUCTO_INEXISTENTE)` (no se saltea) | U |

## R2 — Talles

| Partición | Límites / valores | Caso | Esperado | Nivel |
|---|---|---|---|---|
| Talle válido exacto | `XS S M L XL XXL` | `validar_item(item("buzo","XXL",1))` | no lanza | U |
| Talle en minúscula / mixto | `"m"`, `"xxl"`, `"Xs"` | `calcular_subtotal([item("buzo","m",1)])` | `24999.90` | U |
| Espacios alrededor | `"  M "`, `"\tl\n"` | `calcular_subtotal([item("buzo","  M ",1)])` | `24999.90` | U |
| Talle fuera de la lista | `"XXXL"`, `"mediano"` | `validar_item(item("buzo","XXXL",1))` | `err(TALLE_INVALIDO)` | U |
| Vacío o solo espacios | `""`, `"   "` | `validar_item(item("buzo","",1))` | `err(TALLE_INVALIDO)` | U |
| Espacio en el medio | `"M L"`, `"X S"` | `validar_item(item("buzo","X S",1))` | `err(TALLE_INVALIDO)` | U |
| Talle de otro tipo | `None`, `3`, `["M"]` | `validar_item(item("buzo",None,1))` | `err(TALLE_INVALIDO)` | U |
| Ítem sin clave talle | — | `validar_item({"producto":"buzo","cantidad":1})` | `err(TALLE_INVALIDO)` | U |
| Mensaje | `"XXXL"` | `.mensaje` | `"Talle inválido: 'XXXL'"` | U / E |
| Talle se guarda normalizado | `" m "` | `guardar_pedido` → `items[0]["talle"]` | `"M"` | I |

## R3 — Cantidad

| Partición | Límites / valores | Caso | Esperado | Nivel |
|---|---|---|---|---|
| Entero en rango | **0 \| 1**, 2, 9, **10 \| 11** | `calcular_subtotal([item("remera","M",1)])` | `11999.50` | U |
| | borde superior | `calcular_subtotal([item("remera","M",10)])` | `119995.00` | U |
| Debajo del mínimo | `0`, `-1` | `validar_item(item("buzo","M",0))` | `err(CANTIDAD_INVALIDA)` | U |
| Encima del máximo | `11`, `100` | `validar_item(item("buzo","M",11))` | `err(CANTIDAD_INVALIDA)` | U |
| No entero numérico | `2.5`, `2.0`, `Decimal("2")` | `validar_item(item("buzo","M",2.5))` | `err(CANTIDAD_INVALIDA)` | U |
| Entero pero en texto | `"2"` | `validar_item(item("buzo","M","2"))` | `err(CANTIDAD_INVALIDA)` | U |
| Booleano (es int en Python) | `True` | `validar_item(item("buzo","M",True))` | `err(CANTIDAD_INVALIDA)` | U |
| Otros tipos / falta | `None`, `[1]`, sin clave | `validar_item({"producto":"buzo","talle":"M"})` | `err(CANTIDAD_INVALIDA)` | U |
| Orden: talle antes que cantidad | talle y cantidad malos | `validar_item(item("buzo","XXXL",0))` | `err(TALLE_INVALIDO)` | U |

## R4 — Carrito

| Partición | Límites / valores | Caso | Esperado | Nivel |
|---|---|---|---|---|
| Carrito con ítems | 1 ítem (mínimo) | `calcular_subtotal([item("buzo","M",1)])` | `24999.90` | U |
| Varios ítems | 3 ítems | `buzo×1 + remera×2 + campera×1` | `96998.89` | U |
| Carrito vacío | `[]` (0 ítems) | `calcular_subtotal([])` | `err(CARRITO_VACIO)` | U |
| No es lista | `None`, `"buzo"`, `{}` | `calcular_subtotal(None)` | `err(CARRITO_VACIO)` | U |
| Vacío se informa primero | vacío + zona y cupón malos | `calcular_total([], "LUNA", "TRUCHO")` | `err(CARRITO_VACIO)` | U |
| No se modifica el carrito | talles en minúscula + `precio` | `calcular_total(c, "CABA")`, comparar con copia profunda | `c` sin cambios | U |
| No se modifica el ítem | `"xs"` | `validar_item(it)`, comparar con copia | `it` sin cambios | U |
| Vacío por HTTP | `"carrito": []` | `POST /api/v1/pedidos` | `422 CARRITO_VACIO` | E |

## R5 — Descuento por cantidad

| Partición | Límites / valores | Caso | Esperado | Nivel |
|---|---|---|---|---|
| Menos de 5 prendas | 1, **4 \| 5** | `calcular_descuento(D("100000"), 4, None, f)` | `0.00` | U |
| 5 prendas o más | **5**, 6, 50 | `calcular_descuento(D("100000"), 5, None, f)` | `10000.00` | U |
| Suma entre ítems | 2 + 3 = 5 | `calcular_total([remera×2, remera S×3], "RETIRO")` | `descuento 5999.75`, `total 53997.75` | U |
| Redondeo del 10% | 239.999,95 → 23.999,995 | `calcular_total([campera×5], "INTERIOR")` | `descuento 24000.00` | U |

## R6 — Cupones

| Partición | Límites / valores | Caso | Esperado | Nivel |
|---|---|---|---|---|
| EGRESADOS2026 vigente | 01/01, 29/11, **30/11** | `calcular_descuento(D("100000"),1,"EGRESADOS2026",date(2026,11,30))` | `15000.00` | U |
| EGRESADOS2026 vencido | **01/12** \| 2027 | `calcular_descuento(D("100000"),1,"EGRESADOS2026",date(2026,12,1))` | `err(CUPON_VENCIDO)` | U |
| BIENVENIDA con mínimo | **20000.00** | `calcular_descuento(D("20000.00"),1,"BIENVENIDA",f)` | `3000.00` | U |
| BIENVENIDA bajo el mínimo | **19999.99**, 0 | `calcular_descuento(D("19999.99"),1,"BIENVENIDA",f)` | `err(CUPON_MINIMO_NO_ALCANZADO)` | U |
| BIENVENIDA no vence | 2030 | `calcular_descuento(D("20000"),1,"BIENVENIDA",date(2030,1,1))` | `3000.00` | U |
| Mayúsculas / espacios | `"egresados2026"`, `" Bienvenida\t"` | `calcular_descuento(D("100000"),1,"  Egresados2026  ",f)` | `15000.00` | U |
| Sin cupón | `None`, `""`, `"   "` | `calcular_descuento(D("30000"),1,"",f)` | `0.00` (no es error) | U |
| Cupón inexistente | `"XYZ"`, `"EGRESADOS2025"`, `"DEBUG100"` | `calcular_descuento(D("100000"),1,"DEBUG100",f)` | `err(CUPON_INVALIDO)` | U |
| Cupón de otro tipo | `123`, `True` | `calcular_descuento(D("100000"),1,123,f)` | `err(CUPON_INVALIDO)` | U |
| No acumula — gana cupón | 6 prendas + 15% | `calcular_descuento(D("100000"),6,"EGRESADOS2026",f)` | `15000.00` (no 25.000) | U |
| No acumula — gana cantidad | 5 prendas + BIENVENIDA | `calcular_descuento(D("50000"),5,"BIENVENIDA",f)` | `5000.00` (no 8.000) | U |
| Descuento ≤ subtotal | — | todo descuento devuelto | `≤ subtotal` | U |
| Fecha por defecto = día de la llamada | hoy = 01/12/2026 | `calcular_descuento(D("100000"),1,"EGRESADOS2026")` | `err(CUPON_VENCIDO)` | U |
| | hoy = 30/11/2026 | ídem | `15000.00` | U |
| Cupón se guarda normalizado | `"  egresados2026 "` / `""` | `guardar_pedido` → `cupon` | `"EGRESADOS2026"` / `None` | I |
| Fecha por HTTP | `"2026-11-30"` / `"2026-12-01"` | `POST` con cupón | `201 descuento "1799.93"` / `422 CUPON_VENCIDO` | E |

## R7 — Dinero y redondeo

| Partición | Límites / valores | Caso | Esperado | Nivel |
|---|---|---|---|---|
| Importes son Decimal | — | `type(calcular_subtotal([item("buzo","M",1)]))` | `Decimal` | U |
| Precio no representable en float | 24999.90 | `calcular_subtotal([item("buzo","M",1)])` | `== Decimal("24999.90")` exacto | U |
| Medio centavo sube | x,xx5 | `calcular_descuento(D("11999.50"),1,"EGRESADOS2026",f)` | `1799.93` | U |
| | | 15% de 61.999,30 = 9.299,895 | `9299.90` | U |
| Sin medio centavo | exacto | 15% de 249.999,00 | `37499.85` | U |
| Dos decimales siempre | `0`, `2500` | `str(...)` de descuento y envío | `"0.00"`, `"2500.00"` | U |
| Sin pérdida al persistir | 1799.93, 12699.57 | `obtener_pedido` tras `guardar_pedido` | mismos `Decimal`, `str` idéntico | I |
| Montos por HTTP como texto | — | `POST` / `GET` | `"11999.50"`, nunca `11999.5` | E |

## R8 — Envío

| Partición | Límites / valores | Caso | Esperado | Nivel |
|---|---|---|---|---|
| Envío pago: base < 60.000 | **59999.99** | `calcular_envio(D("59999.99"), "CABA")` | `2500.00` | U |
| Envío gratis: base ≥ 60.000 | **60000.00**, 60000.01 | `calcular_envio(D("60000.00"), "CABA")` | `0.00` | U |
| Cada zona | CABA, GBA, INTERIOR, RETIRO | `calcular_envio(D("1000"), "INTERIOR")` | `6500.00` (GBA 4000.00, RETIRO 0.00) | U |
| Zona en minúscula / espacios | `"gba"`, `" gba "`, `"Interior\n"` | `calcular_envio(D("1000"), " gba ")` | `4000.00` | U |
| Zona inexistente | `"LUNA"`, `"CAPITAL"`, `"C ABA"` | `calcular_envio(D("1000"), "LUNA")` | `err(ZONA_INVALIDA)` | U |
| Zona vacía | `""`, `"   "` | `calcular_envio(D("1000"), "")` | `err(ZONA_INVALIDA)` | U |
| Zona de otro tipo | `None`, `1` | `calcular_envio(D("1000"), None)` | `err(ZONA_INVALIDA)` | U |
| Base = subtotal **con** descuento | subtotal ≥ 60k, base < 60k | `calcular_total([buzo×2, remera×1], "CABA", "EGRESADOS2026", f)` | `envio 2500.00` (base 52.699,40) | U |
| Gratis con descuento por cantidad | base 215.999,95 | `calcular_total([campera×5], "INTERIOR")` | `envio 0.00` | U |
| Zona se guarda normalizada | `" caba "` | `guardar_pedido` → `zona` | `"CABA"` | I |

## R9 — Total

| Partición | Límites / valores | Caso | Esperado | Nivel |
|---|---|---|---|---|
| Sin descuento, con envío | ejemplo §5 | `calcular_total([buzo×2], "CABA")` | `49999.80 / 0.00 / 2500.00 / 52499.80` | U |
| Con cupón % y envío | | `calcular_total([remera×1], "CABA", "EGRESADOS2026", 30/11)` | `11999.50 / 1799.93 / 2500.00 / 12699.57` | U |
| Con cupón fijo | | `calcular_total([remera×2], " gba ", "bienvenida", f)` | `23999.00 / 3000.00 / 4000.00 / 24999.00` | U |
| Con envío gratis | | `calcular_total([buzo×10], "RETIRO", "EGRESADOS2026", f)` | `249999.00 / 37499.85 / 0.00 / 212499.15` | U |
| Orden de validación (§3) | ítem 2 talle malo, ítem 3 producto malo | `calcular_total(c, "CABA")` | `err(TALLE_INVALIDO)` | U |
| | ítem malo + cupón malo | `calcular_total([cantidad 11], "LUNA", "TRUCHO")` | `err(CANTIDAD_INVALIDA)` | U |
| | cupón malo + zona mala | `calcular_total([ok], "LUNA", "TRUCHO", f)` | `err(CUPON_INVALIDO)` | U |
| | cupón vencido / mínimo + zona mala | `calcular_total([ok], "LUNA", "EGRESADOS2026", 01/12)` | `err(CUPON_VENCIDO)` | U |
| | solo zona mala | `calcular_total([ok], "LUNA", "EGRESADOS2026", f)` | `err(ZONA_INVALIDA)` | U |

## R10 — Persistencia

Una fila por oración de la regla.

| Oración de R10 | Partición / límites | Caso | Esperado | Nivel |
|---|---|---|---|---|
| Error de checkout se propaga y no guarda nada | talle, carrito vacío, zona, cupón inválido, cupón vencido | `guardar_pedido(con, ..., [ok, talle "XXXL"], "CABA")` | `CheckoutError`; `COUNT(*)` de pedidos e ítems = 0 (leído desde otra conexión) | I |
| | error y después pedido válido | guardar con `cantidad 0`, luego uno válido | solo existe el válido | I |
| Al terminar, el pedido es definitivo | otra conexión abierta | `guardar_pedido` y `obtener_pedido` desde otra conexión | importes e ítems completos | I |
| | conexión cerrada | guardar, cerrar, abrir nueva | pedido completo | I |
| Montos idénticos a checkout | 1799.93 / 12699.57 | `obtener_pedido` vs `calcular_total` | mismos `Decimal`, `str` idéntico, `type is Decimal` | I |
| | `precio_unitario` | buzo, campera | `"24999.90"`, `"47999.99"` | I |
| `precio_unitario` del catálogo | ítem con `precio=1` | `obtener_pedido(...)["items"]` | precio del catálogo | I |
| Datos normalizados | email `"  Ana@Mail.COM "` | fila cruda en SQLite | `"ana@mail.com"` | I |
| | zona `" caba "`, talle `" m "`, cupón `" egresados2026 "` | fila cruda | `"CABA"`, `"M"`, `"EGRESADOS2026"` | I |
| | cupón `None`, `""`, `"   "` | fila cruda | `NULL` / `None` | I |
| `obtener_pedido` de id inexistente | base vacía, id = último + 1 | `obtener_pedido(con, 999)` | `None` | I |
| `pedidos_de` sin mayúsculas ni espacios | `"  aNa@MAIL.com\t"` | `pedidos_de(con, ...)` | los pedidos de ana, no los de beto | I |
| | email sin pedidos | `pedidos_de(con, "nadie@mail.com")` | `[]` | I |
| Del más reciente al más antiguo | 3 pedidos intercalados con otro email | `pedidos_de` | ids en orden descendente | I |
| El email no altera la consulta | `"x' OR '1'='1"`, `"' OR 1=1 --"` | `pedidos_de(con, ...)` con otros pedidos guardados | `[]` | I |
| | email legítimo con comilla | `"o'brien@mail.com"` | encuentra su pedido | I |

## R11 — API HTTP

Pocos casos por nivel E2E: cada uno es un flujo completo POST → GET.

| Partición | Límites / valores | Caso | Esperado | Nivel |
|---|---|---|---|---|
| Crear y leer | sin cupón | `POST` remera M, CABA → `GET /pedidos/{id}` | `201` con montos texto; `GET 200` con formato §6 y montos texto | E |
| Crear con cupón y fecha | `"2026-11-30"` | `POST` + `GET` | `201 {"descuento": "1799.93", "total": "12699.57"}` | E |
| Compra grande | 5 prendas + BIENVENIDA + precio propio | `POST` + `GET` | montos iguales en ambas respuestas; precios de catálogo | E |
| Persistencia entre servidores | reinicio | `POST` en un servidor, `GET` en otro sobre la misma base | `200`, pedido completo | E |
| Error de negocio | cada `code` de checkout | `POST` con talle `"XXXL"` | `422 {"error": {"code": "TALLE_INVALIDO", "message": "Talle inválido: 'XXXL'"}}` | E |
| Error no deja rastro | error y luego válido | `POST` inválido, luego válido | el válido recibe `id 1` | E |
| Cuerpo no JSON | `"{esto no"`, vacío, truncado, bytes inválidos | `POST` crudo | `400 JSON_INVALIDO` | E |
| Faltan datos | sin email / zona / carrito | `POST` | `400 DATOS_INCOMPLETOS` | E |
| Tipos incorrectos | email `5`/`null`, zona `1`, carrito texto u objeto, cuerpo lista/texto/número | `POST` | `400 DATOS_INCOMPLETOS` | E |
| Fecha inválida | `"30/11/2026"`, `"2026-13-01"`, `"2026-02-30"`, `"20261130"`, `""`, número | `POST` | `400 FECHA_INVALIDA` | E |
| Fecha vencida | `"2026-12-01"` + EGRESADOS2026 | `POST` | `422 CUPON_VENCIDO` | E |
| Pedido inexistente | `999` | `GET /api/v1/pedidos/999` | `404 PEDIDO_INEXISTENTE` | E |
| Id fuera de rango | `2^63`, 23 dígitos | `GET` | `404 PEDIDO_INEXISTENTE` (nunca 500) | E |
| Ruta inexistente | `/`, `/api/v1/pedidos` (GET), `/pedidos/abc`, `/pedidos/-1`, `/api/v2/pedidos` | `GET` / `POST` / `DELETE` | `404 RUTA_INEXISTENTE` | E |
| Nunca 500 | cualquier entrada | todos los anteriores | status ∈ {201, 200, 400, 404, 422} | E |
