import copy
import http.client
import json
import threading
from decimal import Decimal

import pytest

import api

PEDIDOS = "/api/v1/pedidos"


# ------------------------------------------------------------------ infraestructura
@pytest.fixture
def servidor(tmp_path):
    """Servidor real, en un puerto libre y con una base SQLite en un archivo."""
    servidor = api.crear_servidor(str(tmp_path / "tienda.db"), 0)
    hilo = threading.Thread(target=servidor.serve_forever, daemon=True)
    hilo.start()
    yield servidor
    servidor.shutdown()
    servidor.server_close()
    hilo.join(timeout=5)


class Respuesta:
    def __init__(self, status, tipo, texto):
        self.status = status
        self.tipo = tipo
        self.texto = texto
        try:
            self.cuerpo = json.loads(texto)
        except ValueError:
            self.cuerpo = None


def pedir(servidor, metodo, ruta, cuerpo=None, crudo=None):
    """Request HTTP real. `cuerpo` se serializa como JSON; `crudo` se manda tal cual."""
    datos = None
    headers = {}
    if crudo is not None:
        datos = crudo
    elif cuerpo is not None:
        datos = json.dumps(cuerpo).encode("utf-8")
    if datos is not None:
        headers["Content-Type"] = "application/json"

    conexion = http.client.HTTPConnection("127.0.0.1", servidor.server_address[1], timeout=10)
    try:
        conexion.request(metodo, ruta, body=datos, headers=headers)
        respuesta = conexion.getresponse()
        texto = respuesta.read().decode("utf-8", errors="replace")
        return Respuesta(respuesta.status, respuesta.getheader("Content-Type"), texto)
    finally:
        conexion.close()


def item(producto="remera", talle="M", cantidad=1):
    return {"producto": producto, "talle": talle, "cantidad": cantidad}


def pedido_valido(**cambios):
    """Cuerpo de la especificación (sección 7), con los cambios que se pidan."""
    cuerpo = {
        "email": "ana@mail.com",
        "zona": "CABA",
        "carrito": [item()],
        "cupon": "EGRESADOS2026",
        "fecha": "2026-11-30",
    }
    cuerpo.update(copy.deepcopy(cambios))
    return cuerpo


def crear(servidor, **cambios):
    return pedir(servidor, "POST", PEDIDOS, cuerpo=pedido_valido(**cambios))


def sin(cuerpo, clave):
    cuerpo = copy.deepcopy(cuerpo)
    del cuerpo[clave]
    return cuerpo


def verificar_error(respuesta, status, code):
    """Todos los errores tienen el mismo formato: {"error": {"code", "message"}}."""
    assert respuesta.status == status, respuesta.texto
    assert respuesta.cuerpo is not None, f"la respuesta no es JSON: {respuesta.texto!r}"
    assert list(respuesta.cuerpo) == ["error"], respuesta.texto
    error = respuesta.cuerpo["error"]
    assert isinstance(error, dict), respuesta.texto
    assert sorted(error) == ["code", "message"], respuesta.texto
    assert error["code"] == code
    assert isinstance(error["message"], str) and error["message"]


# =====================================================================
# POST /api/v1/pedidos
# =====================================================================
def test_post_crea_un_pedido_y_responde_201(servidor):
    respuesta = pedir(servidor, "POST", PEDIDOS, cuerpo=pedido_valido())

    assert respuesta.status == 201, respuesta.texto
    assert respuesta.tipo.startswith("application/json")
    assert respuesta.cuerpo == {
        "id": 1,
        "subtotal": "11999.50",
        "descuento": "1799.93",
        "envio": "2500.00",
        "total": "12699.57",
    }


def test_post_cupon_y_fecha_son_opcionales(servidor):
    cuerpo = {"email": "ana@mail.com", "zona": "CABA", "carrito": [item("buzo", "M", 2)]}

    respuesta = pedir(servidor, "POST", PEDIDOS, cuerpo=cuerpo)

    assert respuesta.status == 201, respuesta.texto
    assert respuesta.cuerpo == {
        "id": 1,
        "subtotal": "49999.80",
        "descuento": "0.00",
        "envio": "2500.00",
        "total": "52499.80",
    }


def test_post_los_montos_viajan_como_texto_nunca_como_numero(servidor):
    respuesta = crear(servidor, carrito=[item("buzo", "M", 3)], cupon=None)

    assert respuesta.status == 201, respuesta.texto
    for campo in ("subtotal", "descuento", "envio", "total"):
        assert isinstance(respuesta.cuerpo[campo], str), campo
    assert Decimal(respuesta.cuerpo["subtotal"]) == Decimal("74999.70")
    assert Decimal(respuesta.cuerpo["total"]) == Decimal("74999.70")  # envío gratis


def test_post_ignora_las_claves_de_mas_y_el_precio_del_cliente(servidor):
    carrito = [{"producto": "remera", "talle": "M", "cantidad": 1, "precio": 1, "color": "rojo"}]

    respuesta = crear(servidor, carrito=carrito, cupon=None)

    assert respuesta.status == 201, respuesta.texto
    assert respuesta.cuerpo["subtotal"] == "11999.50"


# =====================================================================
# GET /api/v1/pedidos/{id}
# =====================================================================
def test_get_devuelve_el_pedido_completo(servidor):
    creado = crear(servidor)
    assert creado.status == 201, creado.texto

    respuesta = pedir(servidor, "GET", f"{PEDIDOS}/{creado.cuerpo['id']}")

    assert respuesta.status == 200, respuesta.texto
    assert respuesta.tipo.startswith("application/json")
    assert respuesta.cuerpo == {
        "id": 1,
        "email": "ana@mail.com",
        "zona": "CABA",
        "cupon": "EGRESADOS2026",
        "subtotal": "11999.50",
        "descuento": "1799.93",
        "envio": "2500.00",
        "total": "12699.57",
        "items": [
            {"producto": "remera", "talle": "M", "cantidad": 1, "precio_unitario": "11999.50"},
        ],
    }


def test_get_devuelve_cada_pedido_con_sus_propios_datos(servidor):
    primero = crear(servidor, email="ana@mail.com", carrito=[item("buzo", "S", 2)], cupon=None)
    segundo = crear(servidor, email="beto@mail.com", carrito=[item("campera", "L", 1)], cupon=None)
    assert (primero.status, segundo.status) == (201, 201)
    assert primero.cuerpo["id"] != segundo.cuerpo["id"]

    uno = pedir(servidor, "GET", f"{PEDIDOS}/{primero.cuerpo['id']}").cuerpo
    dos = pedir(servidor, "GET", f"{PEDIDOS}/{segundo.cuerpo['id']}").cuerpo

    assert uno["email"] == "ana@mail.com"
    assert [(i["producto"], i["talle"], i["cantidad"]) for i in uno["items"]] == [("buzo", "S", 2)]
    assert dos["email"] == "beto@mail.com"
    assert [(i["producto"], i["talle"], i["cantidad"]) for i in dos["items"]] == [("campera", "L", 1)]
    assert dos["total"] == "50499.99"


def test_flujo_completo_los_datos_se_guardan_normalizados(servidor):
    creado = pedir(
        servidor,
        "POST",
        PEDIDOS,
        cuerpo={
            "email": "  Ana@Mail.COM ",
            "zona": " caba ",
            "carrito": [item("remera", " m ", 2), item("buzo", "xl", 1)],
            "cupon": " egresados2026 ",
            "fecha": "2026-10-01",
        },
    )
    assert creado.status == 201, creado.texto

    pedido = pedir(servidor, "GET", f"{PEDIDOS}/{creado.cuerpo['id']}").cuerpo

    assert pedido["email"] == "ana@mail.com"
    assert pedido["zona"] == "CABA"
    assert pedido["cupon"] == "EGRESADOS2026"
    assert [i["talle"] for i in pedido["items"]] == ["M", "XL"]
    assert pedido["subtotal"] == "48998.90"
    assert pedido["total"] == creado.cuerpo["total"]


# =====================================================================
# R11 · Error de negocio (CheckoutError) → 422 con su code
# =====================================================================
@pytest.mark.parametrize(
    "cambios, codigo",
    [
        ({"carrito": []}, "CARRITO_VACIO"),
        ({"carrito": [item("zapato")]}, "PRODUCTO_INEXISTENTE"),
        ({"carrito": [item(talle="XXXL")]}, "TALLE_INVALIDO"),
        ({"carrito": [item(cantidad=11)]}, "CANTIDAD_INVALIDA"),
        ({"cupon": "NOEXISTE"}, "CUPON_INVALIDO"),
        ({"fecha": "2026-12-01"}, "CUPON_VENCIDO"),
        ({"cupon": "BIENVENIDA"}, "CUPON_MINIMO_NO_ALCANZADO"),
        ({"zona": "MARTE"}, "ZONA_INVALIDA"),
    ],
)
def test_error_de_negocio_devuelve_422_con_el_code_del_checkout_error(servidor, cambios, codigo):
    respuesta = crear(servidor, **cambios)

    verificar_error(respuesta, 422, codigo)


def test_error_de_negocio_trae_el_mensaje_del_contrato(servidor):
    respuesta = crear(servidor, carrito=[item(talle="XXXL")])

    verificar_error(respuesta, 422, "TALLE_INVALIDO")
    assert respuesta.cuerpo["error"]["message"] == "Talle inválido: 'XXXL'"


def test_error_de_negocio_no_deja_ningun_pedido_guardado(servidor):
    verificar_error(crear(servidor, carrito=[item("zapato")]), 422, "PRODUCTO_INEXISTENTE")

    verificar_error(pedir(servidor, "GET", f"{PEDIDOS}/1"), 404, "PEDIDO_INEXISTENTE")


# =====================================================================
# R11 · El cuerpo no es JSON válido → 400 JSON_INVALIDO
# =====================================================================
@pytest.mark.parametrize(
    "crudo",
    [b"esto no es json", b"{", b'{"email": "ana@mail.com",}', b"", b"\xff\xfe\x00"],
)
def test_cuerpo_que_no_es_json_devuelve_400(servidor, crudo):
    respuesta = pedir(servidor, "POST", PEDIDOS, crudo=crudo)

    verificar_error(respuesta, 400, "JSON_INVALIDO")


# =====================================================================
# R11 · Falta email, zona o carrito, o tienen otro tipo → 400 DATOS_INCOMPLETOS
# =====================================================================
@pytest.mark.parametrize("clave", ["email", "zona", "carrito"])
def test_falta_un_dato_obligatorio_devuelve_400(servidor, clave):
    respuesta = pedir(servidor, "POST", PEDIDOS, cuerpo=sin(pedido_valido(), clave))

    verificar_error(respuesta, 400, "DATOS_INCOMPLETOS")


@pytest.mark.parametrize(
    "cambios",
    [
        {"email": 123},
        {"email": None},
        {"email": ["ana@mail.com"]},
        {"zona": 5},
        {"zona": None},
        {"zona": {"nombre": "CABA"}},
        {"carrito": "buzo"},
        {"carrito": None},
        {"carrito": {"producto": "buzo", "talle": "M", "cantidad": 1}},
    ],
)
def test_dato_obligatorio_de_otro_tipo_devuelve_400(servidor, cambios):
    respuesta = crear(servidor, **cambios)

    verificar_error(respuesta, 400, "DATOS_INCOMPLETOS")


@pytest.mark.parametrize("crudo", [b"[]", b"[1, 2, 3]", b'"hola"', b"42", b"null", b"{}"])
def test_cuerpo_json_que_no_es_un_objeto_con_datos_devuelve_400(servidor, crudo):
    respuesta = pedir(servidor, "POST", PEDIDOS, crudo=crudo)

    verificar_error(respuesta, 400, "DATOS_INCOMPLETOS")



# =====================================================================
# R11 · El pedido no existe → 404 PEDIDO_INEXISTENTE
# =====================================================================
def test_pedido_inexistente_devuelve_404(servidor):
    respuesta = pedir(servidor, "GET", f"{PEDIDOS}/999")

    verificar_error(respuesta, 404, "PEDIDO_INEXISTENTE")


def test_pedido_inexistente_aunque_haya_otros_guardados(servidor):
    creado = crear(servidor)
    assert creado.status == 201, creado.texto

    respuesta = pedir(servidor, "GET", f"{PEDIDOS}/{creado.cuerpo['id'] + 1}")

    verificar_error(respuesta, 404, "PEDIDO_INEXISTENTE")


@pytest.mark.parametrize("numero", ["0", "9223372036854775808", "99999999999999999999999"])
def test_id_enorme_o_cero_devuelve_404_y_no_500(servidor, numero):
    respuesta = pedir(servidor, "GET", f"{PEDIDOS}/{numero}")

    verificar_error(respuesta, 404, "PEDIDO_INEXISTENTE")

