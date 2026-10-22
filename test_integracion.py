from datetime import date
from decimal import Decimal

import pytest

import pedidos
from checkout import CheckoutError, calcular_total

HOY_VIGENTE = date(2026, 10, 1)
DESPUES_DEL_VENCIMIENTO = date(2026, 12, 1)


@pytest.fixture
def ruta(tmp_path):
    return str(tmp_path / "tienda.db")


@pytest.fixture
def con(ruta):
    conexion = pedidos.conectar(ruta)
    pedidos.crear_esquema(conexion)
    yield conexion
    conexion.close()


def item(producto="buzo", talle="M", cantidad=1, **extra):
    return {"producto": producto, "talle": talle, "cantidad": cantidad, **extra}


def contar(ruta, tabla):
    """Cuenta filas desde OTRA conexión: solo ve lo que quedó confirmado."""
    assert tabla in ("pedidos", "items")
    otra = pedidos.conectar(ruta)
    try:
        return otra.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0]
    finally:
        otra.close()


def contar_en(con, tabla):
    """Cuenta filas desde la MISMA conexión: ve también lo no confirmado."""
    assert tabla in ("pedidos", "items")
    return con.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0]


def guardar(con, email="ana@mail.com", carrito=None, zona="CABA", cupon=None, fecha=HOY_VIGENTE):
    if carrito is None:
        carrito = [item()]
    return pedidos.guardar_pedido(con, email, carrito, zona, cupon, fecha)


# Carrito cuyos importes se pueden representar exactamente incluso como float
# (35998.50 y 2500). Sirve para probar una regla sin mezclarla con la de Decimal.
CARRITO_EXACTO = [item("remera", "M", 2), item("remera", "L", 1)]


# =====================================================================
# R10 · Si calcular_total lanza CheckoutError, el error se propaga y
#       no queda nada guardado: ni el pedido ni sus ítems.
# =====================================================================
@pytest.mark.parametrize(
    "carrito, zona, cupon, fecha, codigo",
    [
        ([], "CABA", None, HOY_VIGENTE, "CARRITO_VACIO"),
        ([item("zapato")], "CABA", None, HOY_VIGENTE, "PRODUCTO_INEXISTENTE"),
        ([item(talle="XXXL")], "CABA", None, HOY_VIGENTE, "TALLE_INVALIDO"),
        ([item(cantidad=11)], "CABA", None, HOY_VIGENTE, "CANTIDAD_INVALIDA"),
        ([item()], "CABA", "NOEXISTE", HOY_VIGENTE, "CUPON_INVALIDO"),
        ([item()], "CABA", "EGRESADOS2026", DESPUES_DEL_VENCIMIENTO, "CUPON_VENCIDO"),
        ([item("remera")], "CABA", "BIENVENIDA", HOY_VIGENTE, "CUPON_MINIMO_NO_ALCANZADO"),
        ([item()], "MARTE", None, HOY_VIGENTE, "ZONA_INVALIDA"),
    ],
)
def test_error_de_negocio_se_propaga_y_no_queda_nada_guardado(
    con, ruta, carrito, zona, cupon, fecha, codigo
):
    with pytest.raises(CheckoutError) as error:
        pedidos.guardar_pedido(con, "ana@mail.com", carrito, zona, cupon, fecha)

    assert error.value.code == codigo
    assert contar(ruta, "pedidos") == 0
    assert contar(ruta, "items") == 0


def test_un_error_no_deja_basura_ni_afecta_a_los_pedidos_ya_guardados(con):
    id_bueno = guardar(con, carrito=[item("buzo", "M", 2), item("remera", "S", 1)])

    with pytest.raises(CheckoutError):
        guardar(con, carrito=[item("buzo"), item("zapato")])

    assert contar_en(con, "pedidos") == 1
    assert contar_en(con, "items") == 2
    assert pedidos.obtener_pedido(con, id_bueno)["id"] == id_bueno


def test_despues_de_un_error_se_puede_seguir_guardando(con, ruta):
    with pytest.raises(CheckoutError):
        guardar(con, carrito=[])

    nuevo = guardar(con, carrito=[item("remera", "M", 1)])

    assert contar(ruta, "pedidos") == 1
    assert pedidos.obtener_pedido(con, nuevo)["items"][0]["producto"] == "remera"


# =====================================================================
# R10 · Cuando guardar_pedido termina, el pedido es definitivo: otra
#       conexión a la misma base lo ve completo, con todos sus ítems.
# =====================================================================
def test_otra_conexion_ve_todos_los_items_del_pedido(con, ruta):
    guardar(con, carrito=CARRITO_EXACTO)  # `con` sigue abierta: no se hizo commit extra

    assert contar(ruta, "pedidos") == 1
    assert contar(ruta, "items") == 2


def test_otra_conexion_ve_los_importes_calculados(con, ruta):
    pedido_id = guardar(con, carrito=CARRITO_EXACTO)

    otra = pedidos.conectar(ruta)
    try:
        pedido = pedidos.obtener_pedido(otra, pedido_id)
    finally:
        otra.close()

    assert pedido["subtotal"] == Decimal("35998.50")
    assert pedido["descuento"] == Decimal("0.00")
    assert pedido["envio"] == Decimal("2500.00")
    assert pedido["total"] == Decimal("38498.50")


def test_otra_conexion_ve_el_pedido_completo(con, ruta):
    pedido_id = guardar(con, email="Ana@Mail.com", carrito=CARRITO_EXACTO, zona="gba")

    otra = pedidos.conectar(ruta)
    try:
        pedido = pedidos.obtener_pedido(otra, pedido_id)
    finally:
        otra.close()

    assert pedido == {
        "id": pedido_id,
        "email": "ana@mail.com",
        "zona": "GBA",
        "cupon": None,
        "subtotal": Decimal("35998.50"),
        "descuento": Decimal("0.00"),
        "envio": Decimal("4000.00"),
        "total": Decimal("39998.50"),
        "items": [
            {"producto": "remera", "talle": "M", "cantidad": 2, "precio_unitario": Decimal("11999.50")},
            {"producto": "remera", "talle": "L", "cantidad": 1, "precio_unitario": Decimal("11999.50")},
        ],
    }


# =====================================================================
# R10 · Los montos que devuelve obtener_pedido son idénticos a los que
#       calculó checkout: Decimal, mismo valor, sin ninguna pérdida.
# =====================================================================
def test_ejemplo_de_la_especificacion(con):
    pedido_id = guardar(
        con, carrito=[item("remera", "M", 1)], zona="CABA", cupon="EGRESADOS2026"
    )

    pedido = pedidos.obtener_pedido(con, pedido_id)

    assert pedido["subtotal"] == Decimal("11999.50")
    assert pedido["descuento"] == Decimal("1799.93")
    assert pedido["envio"] == Decimal("2500.00")
    assert pedido["total"] == Decimal("12699.57")


@pytest.mark.parametrize(
    "carrito, zona, cupon",
    [
        ([item("remera", "M", 1)], "CABA", "EGRESADOS2026"),
        ([item("buzo", "M", 3)], "CABA", None),
        ([item("campera", "L", 2), item("buzo", "S", 1)], "INTERIOR", "BIENVENIDA"),
        ([item("buzo", "XL", 7)], "GBA", "egresados2026"),
        ([item("campera", "M", 1), item("remera", "XS", 3)], "RETIRO", None),
    ],
)
def test_los_montos_son_identicos_a_los_que_calculo_checkout(con, carrito, zona, cupon):
    esperado = calcular_total(carrito, zona, cupon, HOY_VIGENTE)

    pedido_id = guardar(con, carrito=carrito, zona=zona, cupon=cupon)
    pedido = pedidos.obtener_pedido(con, pedido_id)

    for campo in ("subtotal", "descuento", "envio", "total"):
        assert isinstance(pedido[campo], Decimal), campo
        assert pedido[campo] == esperado[campo], campo


def test_los_montos_sobreviven_a_una_conexion_nueva(con, ruta):
    carrito = [item("buzo", "M", 3)]
    esperado = calcular_total(carrito, "CABA", None, HOY_VIGENTE)
    pedido_id = guardar(con, carrito=carrito)
    con.commit()  # aquí se aísla la pérdida de precisión de la falta de commit

    otra = pedidos.conectar(ruta)
    try:
        pedido = pedidos.obtener_pedido(otra, pedido_id)
    finally:
        otra.close()

    assert pedido["subtotal"] == esperado["subtotal"] == Decimal("74999.70")
    assert pedido["envio"] == esperado["envio"] == Decimal("0.00")  # >= 60.000: envío gratis
    assert pedido["total"] == esperado["total"] == Decimal("74999.70")


@pytest.mark.parametrize(
    "producto, precio",
    [("buzo", "24999.90"), ("remera", "11999.50"), ("campera", "47999.99")],
)
def test_precio_unitario_es_decimal_exacto(con, producto, precio):
    pedido_id = guardar(con, carrito=[item(producto, "M", 1)])

    unitario = pedidos.obtener_pedido(con, pedido_id)["items"][0]["precio_unitario"]

    assert isinstance(unitario, Decimal)
    assert unitario == Decimal(precio)


# =====================================================================
# R10 · precio_unitario es el del catálogo, nunca uno enviado por el cliente.
# =====================================================================
def test_precio_unitario_ignora_el_precio_del_cliente(con):
    pedido_id = guardar(con, carrito=[item("remera", "M", 1, precio=1)])

    unitario = pedidos.obtener_pedido(con, pedido_id)["items"][0]["precio_unitario"]

    assert unitario == Decimal("11999.50")


def test_precio_del_cliente_no_cambia_ni_importes_ni_items(con):
    carrito = [item("remera", "M", 2, precio=1), item("remera", "L", 1, precio=0)]

    pedido = pedidos.obtener_pedido(con, guardar(con, carrito=carrito))

    assert pedido["subtotal"] == Decimal("35998.50")
    assert [i["precio_unitario"] for i in pedido["items"]] == [Decimal("11999.50")] * 2
