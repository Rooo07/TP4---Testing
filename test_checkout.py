import copy
from datetime import date
from decimal import Decimal
from unittest.mock import patch

import pytest

import checkout
from checkout import (
    CUPONES,
    CheckoutError,
    calcular_descuento,
    calcular_envio,
    calcular_subtotal,
    calcular_total,
    validar_item,
)

HOY_VIGENTE = date(2026, 10, 1)
ULTIMO_DIA = date(2026, 11, 30)


def item(producto="buzo", talle="M", cantidad=1, **extra):
    return {"producto": producto, "talle": talle, "cantidad": cantidad, **extra}


def codigo_de_error(funcion, *args):
    with pytest.raises(CheckoutError) as error:
        funcion(*args)
    return error.value.code


def fecha_fija(anio, mes, dia):
    """Clase que reemplaza a `date` y simula que hoy es la fecha indicada."""

    class FechaFija(date):
        @classmethod
        def today(cls):
            return date(anio, mes, dia)

    return FechaFija


# ---------------------------------------------------------------- H-01 / R7
def test_cantidad_cero_es_invalida():
    assert codigo_de_error(validar_item, item(cantidad=0)) == "CANTIDAD_INVALIDA"


# R7 · Los importes son Decimal, nunca float.
def test_importes_son_decimal():
    carrito = [item("buzo", "M", 2)]

    resultado = calcular_total(carrito, "CABA")

    assert resultado == {
        "subtotal": Decimal("49999.80"),
        "descuento": Decimal("0.00"),
        "envio": Decimal("2500.00"),
        "total": Decimal("52499.80"),
    }
    assert all(isinstance(valor, Decimal) for valor in resultado.values())


# H-01 · Cada función devuelve Decimal, no solo calcular_total.
def test_cada_funcion_devuelve_decimal():
    assert isinstance(calcular_subtotal([item()]), Decimal)
    assert isinstance(calcular_descuento(Decimal("1000"), 1, None, HOY_VIGENTE), Decimal)
    assert isinstance(calcular_envio(Decimal("1000"), "CABA"), Decimal)
    assert isinstance(calcular_envio(Decimal("70000"), "CABA"), Decimal)


# H-01 · Sin error binario al multiplicar y sumar.
def test_subtotal_exacto_sin_error_de_float():
    assert calcular_subtotal([item("buzo", "M", 3)]) == Decimal("74999.70")
    assert calcular_subtotal([item("remera", "S", 1), item("campera", "L", 1)]) == Decimal("59999.49")


# ------------------------------------------------------------------- H-02
# R7 · El medio centavo redondea hacia arriba (round() lo manda al par: 10.02).
def test_medio_centavo_redondea_hacia_arriba():
    assert calcular_descuento(Decimal("100.25"), 5, None, HOY_VIGENTE) == Decimal("10.03")


# ------------------------------------------------------------------- H-03
def test_precio_del_cliente_se_ignora():
    assert calcular_subtotal([item("buzo", "M", 1, precio=1)]) == Decimal("24999.90")


# ------------------------------------------------------------------- H-04
def test_producto_inexistente_da_error():
    assert codigo_de_error(calcular_subtotal, [item("zapato")]) == "PRODUCTO_INEXISTENTE"


def test_producto_inexistente_no_se_saltea_en_un_carrito_mixto():
    carrito = [item("buzo"), item("zapato")]
    assert codigo_de_error(calcular_subtotal, carrito) == "PRODUCTO_INEXISTENTE"


# §3 · El producto se valida primero (antes que talle y cantidad).
def test_el_producto_se_valida_primero():
    malo = item("zapato", "ZZ", 99)
    assert codigo_de_error(validar_item, malo) == "PRODUCTO_INEXISTENTE"


@pytest.mark.parametrize("producto", [None, 5, ["buzo"], ""])
def test_producto_ausente_o_de_otro_tipo(producto):
    assert codigo_de_error(validar_item, item(producto)) == "PRODUCTO_INEXISTENTE"


# ------------------------------------------------------------------- H-05
def test_cupon_debug100_no_existe():
    assert (
        codigo_de_error(calcular_descuento, 30000, 1, "DEBUG100", HOY_VIGENTE)
        == "CUPON_INVALIDO"
    )


# ------------------------------------------------------------------- H-06
# R4 · Ninguna función modifica el carrito.
def test_validar_item_no_modifica_el_item():
    original = item(talle="m")
    copia = copy.deepcopy(original)

    validar_item(original)

    assert original == copia


def test_calcular_total_no_modifica_el_carrito():
    carrito = [item("buzo", " m ", 2), item("remera", "xl", 1)]
    copia = copy.deepcopy(carrito)

    calcular_total(carrito, "CABA")

    assert carrito == copia


# ------------------------------------------------------------------- H-07
@pytest.mark.parametrize("talle", ["  M ", "m", " xl", "Xxl  "])
def test_talle_ignora_espacios_y_mayusculas(talle):
    validar_item(item(talle=talle))  # no debe lanzar


# ------------------------------------------------------------------- H-08
@pytest.mark.parametrize("talle", [None, 5, ["M"], "", "   "])
def test_talle_de_otro_tipo_o_vacio(talle):
    assert codigo_de_error(validar_item, item(talle=talle)) == "TALLE_INVALIDO"


def test_talle_ausente():
    sin_talle = {"producto": "buzo", "cantidad": 1}
    assert codigo_de_error(validar_item, sin_talle) == "TALLE_INVALIDO"


# ------------------------------------------------------------------- H-09
def test_mensaje_de_talle_invalido_segun_contrato():
    with pytest.raises(CheckoutError) as error:
        validar_item(item(talle="XXXL"))
    assert error.value.mensaje == "Talle inválido: 'XXXL'"


# ------------------------------------------------------------------- H-10
def test_cantidad_diez_es_valida():
    validar_item(item(cantidad=10))  # no debe lanzar CheckoutError


def test_cantidad_uno_es_valida():
    validar_item(item(cantidad=1))


# ------------------------------------------------------------------- H-11
@pytest.mark.parametrize("cantidad", [0, -1, 11, 1.5, 2.0, "2", None, True, [1]])
def test_cantidad_invalida(cantidad):
    assert codigo_de_error(validar_item, item(cantidad=cantidad)) == "CANTIDAD_INVALIDA"


def test_cantidad_ausente():
    sin_cantidad = {"producto": "buzo", "talle": "M"}
    assert codigo_de_error(validar_item, sin_cantidad) == "CANTIDAD_INVALIDA"


# ------------------------------------------------------------------- H-12
def test_carrito_vacio_es_invalido():
    assert codigo_de_error(calcular_total, [], "CABA") == "CARRITO_VACIO"


def test_subtotal_de_carrito_vacio_es_invalido():
    assert codigo_de_error(calcular_subtotal, []) == "CARRITO_VACIO"


# ------------------------------------------------------------------- H-13
# R6 · Sin `fecha` se usa la del día de la llamada, no la del import.
def test_fecha_por_defecto_es_la_del_dia_de_la_llamada():
    with patch.object(checkout, "date", fecha_fija(2026, 12, 1)):
        assert (
            codigo_de_error(calcular_descuento, 10000, 1, "EGRESADOS2026")
            == "CUPON_VENCIDO"
        )

    with patch.object(checkout, "date", fecha_fija(2026, 10, 1)):
        assert calcular_descuento(Decimal("10000"), 1, "EGRESADOS2026") == Decimal("1500.00")


def test_calcular_total_usa_la_fecha_del_dia_de_la_llamada():
    carrito = [item("buzo", "M", 1)]

    with patch.object(checkout, "date", fecha_fija(2026, 12, 1)):
        assert codigo_de_error(calcular_total, carrito, "CABA", "EGRESADOS2026") == "CUPON_VENCIDO"

    with patch.object(checkout, "date", fecha_fija(2026, 10, 1)):
        assert calcular_total(carrito, "CABA", "EGRESADOS2026")["descuento"] == Decimal("3749.99")


# ------------------------------------------------------------------- H-14
def test_cinco_prendas_tienen_descuento_por_cantidad():
    assert calcular_descuento(100000, 5, None, HOY_VIGENTE) == 10000


def test_cuatro_prendas_no_tienen_descuento_por_cantidad():
    assert calcular_descuento(100000, 4, None, HOY_VIGENTE) == 0


# ------------------------------------------------------------------- H-15
@pytest.mark.parametrize("cupon", [None, "", "   "])
def test_cupon_ausente_vacio_o_en_blanco_equivale_a_no_usar_cupon(cupon):
    assert calcular_descuento(Decimal("10000"), 1, cupon, HOY_VIGENTE) == Decimal("0.00")


# ------------------------------------------------------------------- H-16
@pytest.mark.parametrize("cupon", ["egresados2026", "  Egresados2026 ", "EGRESADOS2026"])
def test_cupon_no_distingue_mayusculas_ni_espacios(cupon):
    assert calcular_descuento(Decimal("10000"), 1, cupon, HOY_VIGENTE) == Decimal("1500.00")


# ------------------------------------------------------------------- H-17
# R6 · Válido hasta el 30/11/2026 inclusive.
def test_cupon_vale_el_ultimo_dia():
    assert calcular_descuento(Decimal("10000"), 1, "EGRESADOS2026", ULTIMO_DIA) == Decimal("1500.00")


def test_cupon_vale_el_dia_anterior_al_vencimiento():
    assert calcular_descuento(Decimal("10000"), 1, "EGRESADOS2026", date(2026, 11, 29)) == Decimal("1500.00")


def test_cupon_vence_el_dia_siguiente():
    assert (
        codigo_de_error(calcular_descuento, 10000, 1, "EGRESADOS2026", date(2026, 12, 1))
        == "CUPON_VENCIDO"
    )


# ------------------------------------------------------------------- H-18
# R6 · No se acumulan: se calculan los dos y se aplica el mayor.
def test_descuentos_no_se_acumulan_gana_el_cupon():
    # cantidad: 10 % de 100000 = 10000 · cupón: 15 % = 15000
    assert calcular_descuento(Decimal("100000"), 5, "EGRESADOS2026", HOY_VIGENTE) == Decimal("15000.00")


def test_descuentos_no_se_acumulan_gana_la_cantidad():
    # cantidad: 10 % de 100000 = 10000 · cupón fijo: 3000
    assert calcular_descuento(Decimal("100000"), 5, "BIENVENIDA", HOY_VIGENTE) == Decimal("10000.00")


# ------------------------------------------------------------------- H-19
# R6 · El descuento nunca supera el subtotal.
def test_descuento_no_supera_el_subtotal():
    cupon_enorme = {"tipo": "fijo", "valor": Decimal("50000"), "minimo": Decimal("0")}
    with patch.dict(CUPONES, {"ENORME": cupon_enorme}):
        assert calcular_descuento(Decimal("30000"), 1, "ENORME", HOY_VIGENTE) == Decimal("30000.00")


def test_total_nunca_es_negativo():
    cupon_enorme = {"tipo": "fijo", "valor": Decimal("999999"), "minimo": Decimal("0")}
    with patch.dict(CUPONES, {"ENORME": cupon_enorme}):
        resultado = calcular_total([item("remera", "M", 1)], "RETIRO", "ENORME", HOY_VIGENTE)
    assert resultado["descuento"] == resultado["subtotal"]
    assert resultado["total"] == Decimal("0.00")


# ------------------------------------------------------------------- H-20
@pytest.mark.parametrize("cupon", [5, ["EGRESADOS2026"], 1.5])
def test_cupon_que_no_es_texto(cupon):
    assert codigo_de_error(calcular_descuento, 10000, 1, cupon, HOY_VIGENTE) == "CUPON_INVALIDO"


@pytest.mark.parametrize("zona", [None, 5, ["CABA"]])
def test_zona_que_no_es_texto(zona):
    assert codigo_de_error(calcular_envio, 10000, zona) == "ZONA_INVALIDA"


# ------------------------------------------------------------------- H-21
def test_zona_invalida_da_checkout_error():
    assert codigo_de_error(calcular_envio, 10000, "MARTE") == "ZONA_INVALIDA"


def test_mensaje_de_zona_invalida_lista_las_opciones():
    with pytest.raises(CheckoutError) as error:
        calcular_envio(10000, "LUNA")
    assert error.value.mensaje == "Zona inválida. Opciones: CABA, GBA, INTERIOR, RETIRO"


@pytest.mark.parametrize(
    "zona, esperado",
    [("CABA", "2500"), (" gba ", "4000"), ("Interior", "6500"), ("retiro", "0")],
)
def test_envio_por_zona(zona, esperado):
    assert calcular_envio(Decimal("10000"), zona) == Decimal(esperado)


# ------------------------------------------------------------------- H-22
# R8 · Gratis si el subtotal YA con el descuento aplicado es >= 60.000.
def test_envio_gratis_exactamente_en_60000():
    assert calcular_envio(Decimal("60000.00"), "CABA") == Decimal("0.00")


def test_envio_se_cobra_con_59999_99():
    assert calcular_envio(Decimal("59999.99"), "CABA") == Decimal("2500.00")


def test_envio_se_mide_despues_del_descuento():
    # subtotal 61.999,30 (>= 60.000) pero con 15 % queda en 52.699,40 (< 60.000)
    carrito = [item("buzo", "M", 2), item("remera", "M", 1)]

    resultado = calcular_total(carrito, "CABA", "EGRESADOS2026", HOY_VIGENTE)

    assert resultado == {
        "subtotal": Decimal("61999.30"),
        "descuento": Decimal("9299.90"),
        "envio": Decimal("2500.00"),
        "total": Decimal("55199.40"),
    }


def test_total_con_cupon_y_envio_gratis():
    carrito = [item("campera", "L", 2)]

    resultado = calcular_total(carrito, "INTERIOR", "EGRESADOS2026", HOY_VIGENTE)

    assert resultado == {
        "subtotal": Decimal("95999.98"),
        "descuento": Decimal("14400.00"),
        "envio": Decimal("0.00"),
        "total": Decimal("81599.98"),
    }


# ------------------------------------------------------------------- H-23
def test_no_hay_imports_sin_uso():
    assert not hasattr(checkout, "json")