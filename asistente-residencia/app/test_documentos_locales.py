import tempfile
import unittest
import zipfile
from pathlib import Path

import documentos_locales


def crear_docx(ruta: Path, parrafos: list[str]) -> None:
    cuerpo = "".join(
        f"<w:p><w:r><w:t>{p}</w:t></w:r></w:p>" for p in parrafos
    )
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body>{cuerpo}</w:body></w:document>"
    )
    with zipfile.ZipFile(ruta, "w") as z:
        z.writestr("word/document.xml", xml)


class TestDocumentosLocales(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.carpeta = Path(self.tmp.name) / "ELAM"
        (self.carpeta / "contratos").mkdir(parents=True)
        (self.carpeta / ".oculto").mkdir()
        crear_docx(self.carpeta / "contratos" / "contrato.docx", ["Razón social: Residencia X", "RUT: 00.000.000-0"])
        (self.carpeta / "notas.txt").write_text("Nota de prueba", encoding="utf-8")
        (self.carpeta / "escaneo.pdf").write_bytes(b"%PDF-1.4")
        (self.carpeta / ".oculto" / "secreto.txt").write_text("no debe verse", encoding="utf-8")
        (self.carpeta.parent / "fuera.txt").write_text("fuera de la carpeta", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_listar_omite_ocultos_y_marca_legibles(self):
        archivos = {a["ruta"]: a for a in documentos_locales.listar(self.carpeta)}
        self.assertIn("contratos/contrato.docx", archivos)
        self.assertNotIn(".oculto/secreto.txt", archivos)
        self.assertTrue(archivos["notas.txt"]["legible"])

    def test_leer_docx(self):
        texto = documentos_locales.leer_texto(self.carpeta, "contratos/contrato.docx")
        self.assertIn("Razón social: Residencia X", texto)
        self.assertIn("RUT: 00.000.000-0", texto)

    def test_leer_txt(self):
        self.assertEqual(documentos_locales.leer_texto(self.carpeta, "notas.txt"), "Nota de prueba")

    def test_no_sale_de_la_carpeta(self):
        with self.assertRaises(ValueError):
            documentos_locales.leer_texto(self.carpeta, "../fuera.txt")

    def test_no_lee_ocultos(self):
        with self.assertRaises(ValueError):
            documentos_locales.leer_texto(self.carpeta, ".oculto/secreto.txt")

    def test_pdf_sin_pypdf_da_mensaje_claro(self):
        try:
            import pypdf  # noqa: F401
            self.skipTest("pypdf instalado; la prueba aplica sin él")
        except ImportError:
            with self.assertRaises(ValueError) as ctx:
                documentos_locales.leer_texto(self.carpeta, "escaneo.pdf")
            self.assertIn("pypdf", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
