"""Almacenamiento del asistente ELEAM (SQLite, biblioteca estándar)."""

import sqlite3
from datetime import date
from pathlib import Path

ESQUEMA = """
CREATE TABLE IF NOT EXISTS personal (
    id TEXT PRIMARY KEY,
    nombre TEXT NOT NULL,
    cargo TEXT,
    fecha_ingreso TEXT NOT NULL,
    tipo_contrato TEXT,
    remuneracion_bruta REAL,
    fecha_termino TEXT,
    notas TEXT
);
CREATE TABLE IF NOT EXISTS documentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero TEXT NOT NULL,
    titulo TEXT NOT NULL,
    fecha TEXT NOT NULL,
    version TEXT,
    responsable TEXT,
    ruta TEXT
);
"""

CAMPOS_PERSONAL = (
    "id", "nombre", "cargo", "fecha_ingreso", "tipo_contrato",
    "remuneracion_bruta", "fecha_termino", "notas",
)
CAMPOS_DOCUMENTO = ("numero", "titulo", "fecha", "version", "responsable", "ruta")


def conectar(ruta: Path) -> sqlite3.Connection:
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(ruta)
    con.row_factory = sqlite3.Row
    con.executescript(ESQUEMA)
    return con


def _texto(datos: dict, campo: str, obligatorio: bool = False) -> str | None:
    valor = str(datos.get(campo) or "").strip()
    if obligatorio and not valor:
        raise ValueError(f"El campo '{campo}' es obligatorio")
    return valor or None


def _fecha(datos: dict, campo: str, obligatorio: bool = False) -> str | None:
    valor = _texto(datos, campo, obligatorio)
    if valor is None:
        return None
    try:
        return date.fromisoformat(valor).isoformat()
    except ValueError as e:
        raise ValueError(f"'{campo}' debe tener formato AAAA-MM-DD") from e


def _fila(row) -> dict | None:
    return dict(row) if row else None


# --- Personal ---------------------------------------------------------------

def listar_personal(con) -> list[dict]:
    return [dict(r) for r in con.execute("SELECT * FROM personal ORDER BY nombre")]


def obtener_personal(con, pid: str) -> dict | None:
    return _fila(con.execute("SELECT * FROM personal WHERE id = ?", (pid,)).fetchone())


def guardar_personal(con, datos: dict) -> dict:
    remuneracion = datos.get("remuneracion_bruta")
    try:
        remuneracion = None if remuneracion in (None, "") else float(remuneracion)
    except (TypeError, ValueError) as e:
        raise ValueError("'remuneracion_bruta' debe ser un número") from e
    if remuneracion is not None and remuneracion < 0:
        raise ValueError("'remuneracion_bruta' no puede ser negativa")

    registro = {
        "id": _texto(datos, "id", obligatorio=True),
        "nombre": _texto(datos, "nombre", obligatorio=True),
        "cargo": _texto(datos, "cargo"),
        "fecha_ingreso": _fecha(datos, "fecha_ingreso", obligatorio=True),
        "tipo_contrato": _texto(datos, "tipo_contrato"),
        "remuneracion_bruta": remuneracion,
        "fecha_termino": _fecha(datos, "fecha_termino"),
        "notas": _texto(datos, "notas"),
    }
    if registro["fecha_termino"] and registro["fecha_termino"] < registro["fecha_ingreso"]:
        raise ValueError("La fecha de término es anterior a la de ingreso")

    columnas = ", ".join(CAMPOS_PERSONAL)
    marcadores = ", ".join("?" for _ in CAMPOS_PERSONAL)
    actualizacion = ", ".join(f"{c} = excluded.{c}" for c in CAMPOS_PERSONAL[1:])
    con.execute(
        f"INSERT INTO personal ({columnas}) VALUES ({marcadores}) "
        f"ON CONFLICT(id) DO UPDATE SET {actualizacion}",
        [registro[c] for c in CAMPOS_PERSONAL],
    )
    con.commit()
    return obtener_personal(con, registro["id"])


def eliminar_personal(con, pid: str) -> bool:
    cursor = con.execute("DELETE FROM personal WHERE id = ?", (pid,))
    con.commit()
    return cursor.rowcount > 0


# --- Documentos -------------------------------------------------------------

def listar_documentos(con) -> list[dict]:
    return [dict(r) for r in con.execute("SELECT * FROM documentos ORDER BY fecha DESC, id DESC")]


def agregar_documento(con, datos: dict) -> dict:
    registro = {
        "numero": _texto(datos, "numero", obligatorio=True),
        "titulo": _texto(datos, "titulo", obligatorio=True),
        "fecha": _fecha(datos, "fecha", obligatorio=True),
        "version": _texto(datos, "version"),
        "responsable": _texto(datos, "responsable"),
        "ruta": _texto(datos, "ruta"),
    }
    cursor = con.execute(
        f"INSERT INTO documentos ({', '.join(CAMPOS_DOCUMENTO)}) "
        f"VALUES ({', '.join('?' for _ in CAMPOS_DOCUMENTO)})",
        [registro[c] for c in CAMPOS_DOCUMENTO],
    )
    con.commit()
    return _fila(con.execute("SELECT * FROM documentos WHERE id = ?", (cursor.lastrowid,)).fetchone())
