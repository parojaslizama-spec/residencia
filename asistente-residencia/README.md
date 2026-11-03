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

## Cómo abrir la aplicación

Requiere Python 3. No hay nada que instalar.

```bash
# Solo desde esta PC: http://127.0.0.1:8000
python3 asistente-residencia/app/servidor.py

# Desde el celular (misma Wi‑Fi). Define una clave antes de exponerla en la red.
ASISTENTE_CLAVE="una-clave-larga" python3 asistente-residencia/app/servidor.py --red
```

Los datos se guardan en `asistente-residencia/datos/asistente.db`. Esa carpeta está en `.gitignore` y no se sube al repositorio.

## Pruebas

```bash
python3 -m unittest discover -s asistente-residencia/app -p "test_*.py"
python3 -m unittest discover -s asistente-residencia/calculos -p "test_*.py"
```
