"""Servidor local del asistente ELEAM. Solo biblioteca estándar.

Uso:
    python3 asistente-residencia/app/servidor.py                # solo esta PC (127.0.0.1:8000)
    python3 asistente-residencia/app/servidor.py --red          # accesible desde el celular en la misma Wi‑Fi

Variables de entorno:
    ASISTENTE_CLAVE  Si se define, la API exige esa clave (cabecera X-Clave). Recomendado con --red.
    ASISTENTE_DB     Ruta del archivo SQLite. Por defecto: asistente-residencia/datos/asistente.db
"""

import argparse
import hmac
import json
import os
import socket
import sys
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ.parent / "calculos"))

import db  # noqa: E402
from laboral import aviso_previo, anos_servicio, indemnizacion_anos_servicio  # noqa: E402

ESTATICO = RAIZ / "static" / "index.html"
RUTA_DB = Path(os.environ.get("ASISTENTE_DB", RAIZ.parent / "datos" / "asistente.db"))
CLAVE = os.environ.get("ASISTENTE_CLAVE", "")
TAMANO_MAXIMO = 1_000_000


def costos_despido(persona: dict, hoy: date | None = None) -> dict:
    """Costos orientativos de desvinculación según los supuestos de calculos/laboral.py."""
    ingreso = date.fromisoformat(persona["fecha_ingreso"])
    termino = date.fromisoformat(persona["fecha_termino"]) if persona.get("fecha_termino") else (hoy or date.today())
    bruta = float(persona.get("remuneracion_bruta") or 0)
    anos, meses = anos_servicio(ingreso, termino)
    return {
        "antiguedad": f"{anos} años y {meses} meses",
        "indemnizacion_anos_servicio": indemnizacion_anos_servicio(ingreso, termino, bruta),
        "aviso_previo": aviso_previo(bruta),
        "nota": "Cálculo orientativo. Verificar con un abogado laboral (supuestos en calculos/laboral.py).",
    }


def rutas_api(con, metodo: str, ruta: str, leer) -> tuple[int, object]:
    partes = ruta.strip("/").split("/")  # ["api", recurso, id?, accion?]
    if len(partes) < 2:
        return 404, {"error": "No encontrado"}
    recurso = partes[1]

    if recurso == "personal":
        if len(partes) == 2:
            if metodo == "GET":
                return 200, db.listar_personal(con)
            if metodo == "POST":
                return 201, db.guardar_personal(con, leer())
        elif len(partes) == 3:
            pid = partes[2]
            if metodo == "GET":
                persona = db.obtener_personal(con, pid)
                return (200, persona) if persona else (404, {"error": "No existe"})
            if metodo == "PUT":
                return 200, db.guardar_personal(con, {**leer(), "id": pid})
            if metodo == "DELETE":
                return (200, {"ok": True}) if db.eliminar_personal(con, pid) else (404, {"error": "No existe"})
        elif len(partes) == 4 and partes[3] == "costos" and metodo == "GET":
            persona = db.obtener_personal(con, partes[2])
            if not persona:
                return 404, {"error": "No existe"}
            return 200, costos_despido(persona)

    if recurso == "documentos" and len(partes) == 2:
        if metodo == "GET":
            return 200, db.listar_documentos(con)
        if metodo == "POST":
            return 201, db.agregar_documento(con, leer())

    return 404, {"error": "No encontrado"}


class Manejador(BaseHTTPRequestHandler):
    server_version = "AsistenteELEAM/1.0"

    def _enviar(self, codigo: int, cuerpo: bytes, tipo: str) -> None:
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(cuerpo)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(cuerpo)

    def _json(self, codigo: int, datos) -> None:
        cuerpo = json.dumps(datos, ensure_ascii=False, default=str).encode("utf-8")
        self._enviar(codigo, cuerpo, "application/json; charset=utf-8")

    def _leer(self) -> dict:
        largo = int(self.headers.get("Content-Length") or 0)
        if largo > TAMANO_MAXIMO:
            raise ValueError("Solicitud demasiado grande")
        datos = json.loads(self.rfile.read(largo) or b"{}")
        if not isinstance(datos, dict):
            raise ValueError("Se esperaba un objeto JSON")
        return datos

    def _autorizado(self) -> bool:
        if not CLAVE:
            return True
        return hmac.compare_digest(self.headers.get("X-Clave", ""), CLAVE)

    def _procesar(self, metodo: str) -> None:
        ruta = urlparse(self.path).path
        if metodo == "GET" and ruta == "/":
            return self._enviar(200, ESTATICO.read_bytes(), "text/html; charset=utf-8")
        if not ruta.startswith("/api/"):
            return self._json(404, {"error": "No encontrado"})
        if not self._autorizado():
            return self._json(401, {"error": "Clave incorrecta"})
        con = db.conectar(RUTA_DB)
        try:
            codigo, datos = rutas_api(con, metodo, ruta, self._leer)
            self._json(codigo, datos)
        except ValueError as e:
            self._json(400, {"error": str(e)})
        finally:
            con.close()

    def do_GET(self):
        self._procesar("GET")

    def do_POST(self):
        self._procesar("POST")

    def do_PUT(self):
        self._procesar("PUT")

    def do_DELETE(self):
        self._procesar("DELETE")

    def log_message(self, formato, *args):
        pass  # sin registro de solicitudes: evita escribir datos personales en logs


def ip_local() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("10.255.255.255", 1))
            return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"


def main() -> None:
    parser = argparse.ArgumentParser(description="Asistente ELEAM")
    parser.add_argument("--red", action="store_true", help="escuchar en la red local (para el celular)")
    parser.add_argument("--puerto", type=int, default=8000)
    args = parser.parse_args()

    host = "0.0.0.0" if args.red else "127.0.0.1"
    if args.red and not CLAVE:
        print("Advertencia: --red sin ASISTENTE_CLAVE deja los datos accesibles a cualquiera en la red.")
    servidor = ThreadingHTTPServer((host, args.puerto), Manejador)
    print(f"Asistente ELEAM en http://127.0.0.1:{args.puerto}")
    if args.red:
        print(f"Desde el celular: http://{ip_local()}:{args.puerto}")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
