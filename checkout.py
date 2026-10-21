from datetime import date
from decimal import ROUND_HALF_UP, Decimal
 
 
class CheckoutError(Exception):
    def __init__(self, code, mensaje):
        super().__init__(mensaje)
        self.code = code
        self.mensaje = mensaje
 
 
CATALOGO = {
    "buzo": Decimal("24999.90"),
    "remera": Decimal("11999.50"),
    "campera": Decimal("47999.99"),
}
 
TALLES = ["XS", "S", "M", "L", "XL", "XXL"]
 
CUPONES = {
    "EGRESADOS2026": {
        "tipo": "porcentaje",
        "valor": Decimal("0.15"),
        "vence": date(2026, 11, 30),  # válido hasta ese día inclusive
    },
    "BIENVENIDA": {"tipo": "fijo", "valor": Decimal("3000"), "minimo": Decimal("20000")},
}
 
ENVIOS = {
    "CABA": Decimal("2500"),
    "GBA": Decimal("4000"),
    "INTERIOR": Decimal("6500"),
    "RETIRO": Decimal("0"),
}
 
CANTIDAD_MINIMA_ITEM = 1
CANTIDAD_MAXIMA_ITEM = 10
PRENDAS_PARA_DESCUENTO = 5
DESCUENTO_POR_CANTIDAD = Decimal("0.10")
ENVIO_GRATIS_DESDE = Decimal("60000")
CENTAVO = Decimal("0.01")
 
 
def _a_decimal(valor):
    if isinstance(valor, Decimal):
        return valor
    if isinstance(valor, float):
        return Decimal(str(valor))
    return Decimal(valor)
 
 
def _redondear(importe):
    """Redondeo comercial: el medio centavo siempre sube."""
    return _a_decimal(importe).quantize(CENTAVO, rounding=ROUND_HALF_UP)
 
 
def validar_item(item):
    """Valida un ítem sin modificarlo. El producto se valida primero."""
    producto = item.get("producto") if isinstance(item, dict) else None
    if not isinstance(producto, str) or producto not in CATALOGO:
        raise CheckoutError("PRODUCTO_INEXISTENTE", f"Producto inexistente: {producto!r}")
 
    talle = item.get("talle")
    if isinstance(talle, str):
        talle = talle.strip().upper()
    if talle not in TALLES:
        raise CheckoutError("TALLE_INVALIDO", f"Talle inválido: {talle!r}")
 
    cantidad = item.get("cantidad")
    if (
        isinstance(cantidad, bool)
        or not isinstance(cantidad, int)
        or not (CANTIDAD_MINIMA_ITEM <= cantidad <= CANTIDAD_MAXIMA_ITEM)
    ):
        raise CheckoutError("CANTIDAD_INVALIDA", "La cantidad debe estar entre 1 y 10")
 
 
def calcular_subtotal(carrito):
    if not carrito:
        raise CheckoutError("CARRITO_VACIO", "El carrito no puede estar vacío")
 
    subtotal = Decimal("0")
    for item in carrito:
        validar_item(item)
        # El precio sale siempre del catálogo; un "precio" enviado por el cliente se ignora.
        subtotal += CATALOGO[item["producto"]] * item["cantidad"]
 
    return _redondear(subtotal)
 
 
def calcular_descuento(subtotal, cantidad_prendas, cupon=None, fecha=None):
    """Descuento por cantidad y cupón NO se acumulan: se aplica el mayor,
    y nunca puede superar el subtotal."""
    subtotal = _a_decimal(subtotal)
    if fecha is None:
        fecha = date.today()
 
    por_cantidad = Decimal("0")
    if cantidad_prendas >= PRENDAS_PARA_DESCUENTO:
        por_cantidad = subtotal * DESCUENTO_POR_CANTIDAD
 
    por_cupon = Decimal("0")
    if cupon is not None:
        if not isinstance(cupon, str):
            raise CheckoutError("CUPON_INVALIDO", "El cupón no existe")
 
        codigo = cupon.strip().upper()
        if codigo:  # None, "" o solo espacios equivalen a no usar cupón
            datos = CUPONES.get(codigo)
            if datos is None:
                raise CheckoutError("CUPON_INVALIDO", "El cupón no existe")
 
            vence = datos.get("vence")
            if vence is not None and fecha > vence:
                raise CheckoutError("CUPON_VENCIDO", "El cupón está vencido")
 
            if datos["tipo"] == "porcentaje":
                por_cupon = subtotal * datos["valor"]
            elif datos["tipo"] == "fijo":
                if subtotal <= datos["minimo"]:
                    raise CheckoutError(
                        "CUPON_MINIMO_NO_ALCANZADO",
                        f"El cupón requiere una compra mínima de ${datos['minimo']}",
                    )
                por_cupon = datos["valor"]
 
    descuento = min(max(por_cantidad, por_cupon), subtotal)
    return _redondear(descuento)
 
 
def calcular_envio(importe, zona):
    """`importe` es el subtotal YA con el descuento aplicado.
    El envío es gratis si ese importe es >= 60.000."""
    if not isinstance(zona, str) or zona.strip().upper() not in ENVIOS:
        raise CheckoutError(
            "ZONA_INVALIDA",
            f"Zona inválida. Opciones: {', '.join(ENVIOS)}",
        )
 
    if _a_decimal(importe) >= ENVIO_GRATIS_DESDE:
        return _redondear(0)
 
    return _redondear(ENVIOS[zona.strip().upper()])
 
 
def calcular_total(carrito, zona, cupon=None, fecha=None):
    subtotal = calcular_subtotal(carrito)
    prendas = sum(item["cantidad"] for item in carrito)
 
    descuento = calcular_descuento(subtotal, prendas, cupon, fecha)
    envio = calcular_envio(subtotal - descuento, zona)
    total = _redondear(subtotal - descuento + envio)
 
    return {
        "subtotal": subtotal,
        "descuento": descuento,
        "envio": envio,
        "total": total,
    }