"""Cálculos laborales para el asistente ELEAM.

Supuestos (Chile, Código del Trabajo). Verificar con un abogado laboral antes de
usar en decisiones reales:
- Indemnización por años de servicio: 1 mes de remuneración por año trabajado.
  Una fracción superior a 6 meses cuenta como año completo. Tope de 11 años.
- Aviso previo: 30 días de remuneración cuando no se da el aviso con la antelación legal.
- La remuneración base es la última mensual. El tope de remuneración (en UF) se pasa
  como parámetro porque cambia con el tiempo.
"""

import csv
import sys
from datetime import date
from pathlib import Path

TOPE_ANOS_INDEMNIZACION = 11


def anos_servicio(fecha_ingreso: date, fecha_termino: date) -> tuple[int, int]:
    """Devuelve (años, meses) de servicio completos entre dos fechas."""
    if fecha_termino < fecha_ingreso:
        raise ValueError("La fecha de término es anterior a la de ingreso")
    meses = (fecha_termino.year - fecha_ingreso.year) * 12 + (
        fecha_termino.month - fecha_ingreso.month
    )
    if fecha_termino.day < fecha_ingreso.day:
        meses -= 1
    return meses // 12, meses % 12


def anos_indemnizables(anos: int, meses: int) -> int:
    """Años que cuentan para la indemnización: fracción > 6 meses suma un año, con tope."""
    anos_calc = anos + (1 if meses > 6 else 0)
    return min(anos_calc, TOPE_ANOS_INDEMNIZACION)


def indemnizacion_anos_servicio(
    fecha_ingreso: date,
    fecha_termino: date,
    remuneracion_mensual: float,
    tope_remuneracion: float | None = None,
) -> float:
    """Monto de indemnización por años de servicio.

    tope_remuneracion: si se indica, la remuneración base no supera ese valor
    (en la misma moneda que remuneracion_mensual).
    """
    anos, meses = anos_servicio(fecha_ingreso, fecha_termino)
    base = remuneracion_mensual
    if tope_remuneracion is not None:
        base = min(base, tope_remuneracion)
    return round(anos_indemnizables(anos, meses) * base, 2)


def aviso_previo(remuneracion_mensual: float, dias_avisados: int = 0) -> float:
    """Monto de aviso previo que falta pagar (30 días menos los ya avisados)."""
    faltan = max(0, 30 - dias_avisados)
    return round(remuneracion_mensual * faltan / 30, 2)


def _float(valor: str) -> float:
    return float(valor.replace(".", "").replace(",", ".")) if valor else 0.0


def resumen_despido(fila: dict) -> dict:
    """Calcula costos de despido para una fila del registro de personal."""
    ingreso = date.fromisoformat(fila["fecha_ingreso"])
    termino = date.fromisoformat(fila["fecha_termino"]) if fila.get("fecha_termino") else date.today()
    bruta = _float(fila.get("remuneracion_bruta", ""))
    anos, meses = anos_servicio(ingreso, termino)
    return {
        "id": fila["id"],
        "nombre": fila["nombre"],
        "antiguedad": f"{anos} años y {meses} meses",
        "indemnizacion_anos_servicio": indemnizacion_anos_servicio(ingreso, termino, bruta),
        "aviso_previo_sin_aviso": aviso_previo(bruta),
    }


def main(ruta_csv: str) -> None:
    with open(ruta_csv, newline="", encoding="utf-8") as f:
        filas = [r for r in csv.DictReader(f) if r.get("id")]
    if not filas:
        print("El registro no tiene personal cargado.")
        return
    for fila in filas:
        r = resumen_despido(fila)
        print(
            f"{r['nombre']} ({r['id']}): antigüedad {r['antiguedad']}, "
            f"indemnización {r['indemnizacion_anos_servicio']}, "
            f"aviso previo {r['aviso_previo_sin_aviso']}"
        )


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: laboral.py <registro.csv>")
        sys.exit(1)
    main(sys.argv[1])
