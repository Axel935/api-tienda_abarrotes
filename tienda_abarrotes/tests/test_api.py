from decimal import Decimal


# ---------- Autenticación y autorización ----------
def test_login_correcto_devuelve_token(client, admin):
    r = client.get("/auth/me", headers=admin)
    assert r.status_code == 200 and r.json()["rol"] == "admin"


def test_login_con_password_incorrecta_401(client):
    r = client.post("/auth/login", data={"username": "admin", "password": "mala"})
    assert r.status_code == 401


def test_endpoint_protegido_sin_token_401(client):
    assert client.get("/productos").status_code == 401


def test_token_invalido_401(client):
    r = client.get("/productos", headers={"Authorization": "Bearer abc.def.ghi"})
    assert r.status_code == 401


def test_cajero_no_puede_crear_productos_403(client, cajero):
    r = client.post("/productos", headers=cajero, json={
        "codigo": "X", "nombre": "X", "precio_compra": "1", "precio_venta": "2"})
    assert r.status_code == 403


def test_usuario_duplicado_409(client, admin, cajero):
    r = client.post("/usuarios", headers=admin, json={
        "username": "caja1", "nombre": "Otro", "password": "Cajero1234"})
    assert r.status_code == 409


# ---------- Validaciones de productos ----------
def test_precio_negativo_422(client, admin):
    r = client.post("/productos", headers=admin, json={
        "codigo": "A1", "nombre": "A", "precio_compra": "-1", "precio_venta": "5"})
    assert r.status_code == 422


def test_precio_venta_menor_a_compra_422(client, admin):
    r = client.post("/productos", headers=admin, json={
        "codigo": "A1", "nombre": "A", "precio_compra": "10", "precio_venta": "5"})
    assert r.status_code == 422


def test_codigo_duplicado_409(client, admin, producto):
    r = client.post("/productos", headers=admin, json={
        "codigo": "REF-600", "nombre": "Otro", "precio_compra": "1", "precio_venta": "2"})
    assert r.status_code == 409


def test_producto_inexistente_404(client, admin):
    assert client.get("/productos/9999", headers=admin).status_code == 404


def test_eliminar_producto_es_baja_logica(client, admin, producto):
    assert client.delete(f"/productos/{producto['id']}", headers=admin).status_code == 204
    activos = client.get("/productos", headers=admin).json()
    assert all(p["id"] != producto["id"] for p in activos)
    todos = client.get("/productos?solo_activos=false", headers=admin).json()
    assert any(p["id"] == producto["id"] for p in todos)


# ---------- Proceso central: venta ----------
def test_venta_calcula_total_y_descuenta_stock(client, cajero, admin, producto):
    r = client.post("/ventas", headers=cajero, json={
        "metodo_pago": "efectivo", "items": [{"producto_id": producto["id"], "cantidad": 3}]})
    assert r.status_code == 201
    venta = r.json()
    assert Decimal(venta["total"]) == Decimal("46.50")
    assert venta["estado"] == "COMPLETADA"
    stock = client.get(f"/productos/{producto['id']}", headers=admin).json()["stock"]
    assert stock == 17
    movs = client.get(f"/inventario/movimientos?producto_id={producto['id']}", headers=admin).json()
    assert any(m["tipo"] == "SALIDA_VENTA" and m["cantidad"] == -3 for m in movs)


def test_venta_agrupa_renglones_repetidos(client, cajero, producto):
    r = client.post("/ventas", headers=cajero, json={"metodo_pago": "tarjeta", "items": [
        {"producto_id": producto["id"], "cantidad": 2}, {"producto_id": producto["id"], "cantidad": 3}]})
    assert r.status_code == 201
    assert len(r.json()["detalles"]) == 1 and r.json()["detalles"][0]["cantidad"] == 5


def test_venta_stock_insuficiente_409_y_no_cambia_stock(client, cajero, admin, producto):
    r = client.post("/ventas", headers=cajero, json={
        "metodo_pago": "efectivo", "items": [{"producto_id": producto["id"], "cantidad": 21}]})
    assert r.status_code == 409
    assert client.get(f"/productos/{producto['id']}", headers=admin).json()["stock"] == 20


def test_venta_es_atomica_si_un_renglon_falla(client, cajero, admin, producto):
    r = client.post("/ventas", headers=cajero, json={"metodo_pago": "efectivo", "items": [
        {"producto_id": producto["id"], "cantidad": 2}, {"producto_id": 9999, "cantidad": 1}]})
    assert r.status_code == 404
    assert client.get(f"/productos/{producto['id']}", headers=admin).json()["stock"] == 20


def test_venta_sin_items_422(client, cajero):
    r = client.post("/ventas", headers=cajero, json={"metodo_pago": "efectivo", "items": []})
    assert r.status_code == 422


def test_venta_cantidad_cero_422(client, cajero, producto):
    r = client.post("/ventas", headers=cajero, json={
        "metodo_pago": "efectivo", "items": [{"producto_id": producto["id"], "cantidad": 0}]})
    assert r.status_code == 422


def test_venta_producto_inactivo_409(client, cajero, admin, producto):
    client.delete(f"/productos/{producto['id']}", headers=admin)
    r = client.post("/ventas", headers=cajero, json={
        "metodo_pago": "efectivo", "items": [{"producto_id": producto["id"], "cantidad": 1}]})
    assert r.status_code == 409


def test_cancelar_venta_restaura_stock_y_no_se_repite(client, cajero, admin, producto):
    venta = client.post("/ventas", headers=cajero, json={
        "metodo_pago": "efectivo", "items": [{"producto_id": producto["id"], "cantidad": 4}]}).json()
    assert client.post(f"/ventas/{venta['id']}/cancelar", headers=cajero).status_code == 403
    r = client.post(f"/ventas/{venta['id']}/cancelar", headers=admin)
    assert r.status_code == 200 and r.json()["estado"] == "CANCELADA"
    assert client.get(f"/productos/{producto['id']}", headers=admin).json()["stock"] == 20
    assert client.post(f"/ventas/{venta['id']}/cancelar", headers=admin).status_code == 409


# ---------- Compras, proveedores e inventario ----------
def test_compra_aumenta_stock(client, admin, producto):
    prov = client.post("/proveedores", headers=admin, json={
        "nombre": "Distribuidora Norte", "telefono": "8112345678"}).json()
    r = client.post("/compras", headers=admin, json={"proveedor_id": prov["id"], "items": [
        {"producto_id": producto["id"], "cantidad": 10, "costo_unitario": "9.50"}]})
    assert r.status_code == 201 and Decimal(r.json()["total"]) == Decimal("95.00")
    assert client.get(f"/productos/{producto['id']}", headers=admin).json()["stock"] == 30


def test_compra_con_proveedor_inexistente_404(client, admin, producto):
    r = client.post("/compras", headers=admin, json={"proveedor_id": 999, "items": [
        {"producto_id": producto["id"], "cantidad": 1, "costo_unitario": "1"}]})
    assert r.status_code == 404


def test_proveedor_telefono_invalido_422(client, admin):
    r = client.post("/proveedores", headers=admin, json={"nombre": "X", "telefono": "abc"})
    assert r.status_code == 422


def test_ajuste_que_deja_stock_negativo_409(client, admin, producto):
    r = client.post(f"/productos/{producto['id']}/ajuste-stock", headers=admin,
                    json={"cantidad": -25, "motivo": "merma"})
    assert r.status_code == 409


def test_ajuste_valido_y_stock_bajo(client, admin, producto):
    r = client.post(f"/productos/{producto['id']}/ajuste-stock", headers=admin,
                    json={"cantidad": -16, "motivo": "producto caducado"})
    assert r.status_code == 200 and r.json()["stock"] == 4
    bajos = client.get("/productos/stock-bajo", headers=admin).json()
    assert [p["id"] for p in bajos] == [producto["id"]]
