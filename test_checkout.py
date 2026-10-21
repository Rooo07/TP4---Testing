from datetime import date
from decimal import Decimal

import pytest

from checkout import (
    CheckoutError,
    calcular_descuento,
    calcular_envio,
    calcular_subtotal,
    calcular_total,
    validar_item,
)

HOY_VIGENTE = date(2026, 10, 1)


def item(producto="buzo", talle="M", cantidad=1, **extra):
    return {"producto": producto, "talle": talle, "cantidad": cantidad, **extra}


def codigo_de_error(funcion, *args):
    with pytest.raises(CheckoutError) as error:
        funcion(*args)
    return error.value.code


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

# R3 · Se permiten 10 unidades
def test_cantidad_diez_es_valida():
    validar_item(item(cantidad=10))
    
# R4 · No se debe aceptar el carrito vacio
def test_carrito_vacio_es_invalido():
    assert codigo_de_error(calcular_total, [], "CABA") == "CARRITO_VACIO"
