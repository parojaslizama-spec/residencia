"""Lectura de solo lectura de una carpeta de documentos local (Word, PDF, texto).

Solo lee dentro de la carpeta configurada. Rechaza rutas que salgan de ella
y archivos ocultos. No modifica ni borra nada.
"""

import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime
from pathlib import Path

LEGIBLES = {".docx", ".pdf", ".txt", ".csv", ".md"}
NS_WORD = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def _visible(ruta: Path, carpeta: Path) -> bool:
    return not any(parte.startswith(".") for parte in ruta.relative_to(carpeta).parts)


def listar(carpeta: Path) -> list[dict]:
    carpeta = Path(carpeta)
    if not carpeta.is_dir():
        raise ValueError("La carpeta configurada no existe o no es accesible")
    archivos = []
    for ruta in sorted(carpeta.rglob("*")):
        if not ruta.is_file() or not _visible(ruta, carpeta):
            continue
        stat = ruta.stat()
        archivos.append({
            "ruta": ruta.relative_to(carpeta).as_posix(),
            "tipo": ruta.suffix.lower(),
            "tamano": stat.st_size,
            "modificado": datetime.fromtimestamp(stat.st_mtime).date().isoformat(),
            "legible": ruta.suffix.lower() in LEGIBLES,
        })
    return archivos


def _dentro(carpeta: Path, relativa: str) -> Path:
    destino = (carpeta / relativa).resolve()
    if carpeta.resolve() not in destino.parents or not destino.is_file():
        raise ValueError("Archivo no encontrado en la carpeta de documentos")
    if not _visible(destino, carpeta.resolve()):
        raise ValueError("Archivo no encontrado en la carpeta de documentos")
    return destino


def _texto_docx(ruta: Path) -> str:
    with zipfile.ZipFile(ruta) as z:
        raiz = ET.fromstring(z.read("word/document.xml"))
    parrafos = []
    for p in raiz.iter(f"{NS_WORD}p"):
        parrafos.append("".join(t.text or "" for t in p.iter(f"{NS_WORD}t")))
    return "\n".join(parrafos)


def _texto_pdf(ruta: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as e:
        raise ValueError("Para leer PDF instala pypdf: python -m pip install pypdf") from e
    lector = PdfReader(str(ruta))
    return "\n\n".join((pagina.extract_text() or "") for pagina in lector.pages)


def leer_texto(carpeta: Path, relativa: str, limite: int = 200_000) -> str:
    carpeta = Path(carpeta)
    ruta = _dentro(carpeta, relativa)
    tipo = ruta.suffix.lower()
    if tipo == ".docx":
        texto = _texto_docx(ruta)
    elif tipo == ".pdf":
        texto = _texto_pdf(ruta)
    elif tipo in {".txt", ".csv", ".md"}:
        texto = ruta.read_text(encoding="utf-8", errors="replace")
    else:
        raise ValueError(f"Formato no soportado: {tipo}")
    return texto[:limite]
