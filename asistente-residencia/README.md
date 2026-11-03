# Asistente ELEAM

Base del asistente interno de la residencia ELEAM: documentos, presupuestos, registro de personal y consultas financieras y laborales.

## Alcance

| Módulo | Estado | Descripción |
|---|---|---|
| Registro de personal | Plantilla | `personal/registro_plantilla.csv`: estructura para datos de contrato. Sin datos reales. |
| Cálculos laborales | Base | `calculos/laboral.py`: antigüedad, indemnización por años de servicio y aviso previo. |
| Documentos | Pendiente | Plantillas con el formato de la carpeta de documentos. Requiere ejemplos. |
| Presupuestos | Pendiente | Basado en los simuladores del repo (`index.html`, `control-financiero.html`). |
| Normativa | Pendiente | Resúmenes de normativa aplicable a ELEAM. Orientación, no asesoría legal. |

## Supuestos a confirmar

- **País:** se asume Chile (términos TENS y líquido). Los parámetros de `calculos/laboral.py` deben verificarse con un abogado laboral antes de usarse en decisiones reales.
- **Fuente de datos del personal:** el registro es una plantilla vacía. Los datos reales no deben subirse a un repositorio público.
- **Carpeta de documentos:** `Residencia ancianos` en la PC de Casita aún no está conectada a esta sesión.

## Privacidad

Los datos del personal son personales y sensibles. Antes de cargar datos reales:

1. Confirma que el repositorio sea privado, o guarda los datos fuera del repo.
2. No subas RUT, domicilio, datos de salud ni cuentas bancarias a este repositorio.

## Uso (cálculos laborales)

```bash
python3 asistente-residencia/calculos/laboral.py asistente-residencia/personal/registro_plantilla.csv
python3 -m unittest discover -s asistente-residencia/calculos -p "test_*.py"
```
