import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

import servidor


class TestApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        servidor.RUTA_DB = Path(cls.tmp.name) / "prueba.db"
        servidor.CLAVE = ""
        cls.srv = servidor.ThreadingHTTPServer(("127.0.0.1", 0), servidor.Manejador)
        cls.base = f"http://127.0.0.1:{cls.srv.server_address[1]}"
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        cls.srv.server_close()
        cls.tmp.cleanup()

    def pedir(self, metodo, ruta, datos=None, cabeceras=None):
        cuerpo = json.dumps(datos).encode() if datos is not None else None
        req = urllib.request.Request(self.base + ruta, data=cuerpo, method=metodo, headers=cabeceras or {})
        if cuerpo:
            req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req) as r:
                return r.status, json.loads(r.read() or b"null")
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read() or b"null")

    def test_pagina_principal(self):
        with urllib.request.urlopen(self.base + "/") as r:
            self.assertIn(b"Asistente ELEAM", r.read())

    def test_crear_listar_y_obtener_personal(self):
        codigo, _ = self.pedir("POST", "/api/personal", {
            "id": "1", "nombre": "Ana", "fecha_ingreso": "2018-03-01", "remuneracion_bruta": "900000",
        })
        self.assertEqual(codigo, 201)
        _, lista = self.pedir("GET", "/api/personal")
        self.assertIn("Ana", [p["nombre"] for p in lista])
        _, persona = self.pedir("GET", "/api/personal/1")
        self.assertEqual(persona["remuneracion_bruta"], 900000.0)

    def test_costos_despido(self):
        self.pedir("POST", "/api/personal", {
            "id": "2", "nombre": "Luis", "fecha_ingreso": "2015-01-01",
            "fecha_termino": "2020-01-01", "remuneracion_bruta": 1000000,
        })
        codigo, costos = self.pedir("GET", "/api/personal/2/costos")
        self.assertEqual(codigo, 200)
        self.assertEqual(costos["antiguedad"], "5 años y 0 meses")
        self.assertEqual(costos["indemnizacion_anos_servicio"], 5_000_000)
        self.assertEqual(costos["aviso_previo"], 1_000_000)

    def test_validaciones(self):
        codigo, err = self.pedir("POST", "/api/personal", {"id": "3", "nombre": "", "fecha_ingreso": "2020-01-01"})
        self.assertEqual(codigo, 400)
        self.assertIn("nombre", err["error"])
        codigo, err = self.pedir("POST", "/api/personal", {
            "id": "4", "nombre": "X", "fecha_ingreso": "2020-05-01", "fecha_termino": "2020-01-01",
        })
        self.assertEqual(codigo, 400)
        codigo, _ = self.pedir("POST", "/api/personal", {"id": "5", "nombre": "X", "fecha_ingreso": "no-es-fecha"})
        self.assertEqual(codigo, 400)

    def test_actualizar_y_borrar(self):
        self.pedir("PUT", "/api/personal/1", {"nombre": "Ana María", "fecha_ingreso": "2018-03-01"})
        _, persona = self.pedir("GET", "/api/personal/1")
        self.assertEqual(persona["nombre"], "Ana María")
        self.assertEqual(self.pedir("DELETE", "/api/personal/1")[0], 200)
        self.assertEqual(self.pedir("GET", "/api/personal/1")[0], 404)

    def test_documentos(self):
        codigo, doc = self.pedir("POST", "/api/documentos", {
            "numero": "DOC-001", "titulo": "Presupuesto anual", "fecha": "2026-01-10", "version": "v1",
        })
        self.assertEqual(codigo, 201)
        self.assertEqual(doc["numero"], "DOC-001")
        _, docs = self.pedir("GET", "/api/documentos")
        self.assertEqual(len(docs), 1)

    def test_clave_requerida_cuando_se_define(self):
        servidor.CLAVE = "secreta"
        try:
            self.assertEqual(self.pedir("GET", "/api/personal")[0], 401)
            self.assertEqual(self.pedir("GET", "/api/personal", cabeceras={"X-Clave": "mala"})[0], 401)
            self.assertEqual(self.pedir("GET", "/api/personal", cabeceras={"X-Clave": "secreta"})[0], 200)
        finally:
            servidor.CLAVE = ""


if __name__ == "__main__":
    unittest.main()
