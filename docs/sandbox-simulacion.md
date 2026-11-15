# Sandbox de simulación

Entorno de prueba local para ver cómo reacciona el motor (`core/sync.py` + `core/executor.py`)
ante cambios típicos en una base grande. `sandbox/` está en `.gitignore`: nunca va al remoto.
Lo que sí se versiona es el generador: `tools/sandbox.py`.

## Uso

```bash
python tools/sandbox.py build        # recrea sandbox/origen + sandbox/destino y hace el primer sync
python tools/sandbox.py mutate 1|2|3 # aplica un escenario de cambios al origen
python tools/sandbox.py analyze      # muestra el plan sin tocar nada
python tools/sandbox.py sync         # aplica el plan
python tools/sandbox.py tree destino # lista archivos
python tools/sandbox.py stress       # casos extremos A-G, cada uno sobre un sandbox nuevo
```

No usa la UI ni `%APPDATA%\Arch-Ive` (no toca tus espejos ni el historial reales).
Para verlo en la UI, crea un espejo apuntando a `sandbox/origen` → `sandbox/destino`.

## Cómo se construyó

- 14 archivos falsos (27.7 MB) con estructura tipo CDE: `01_WIP`, `02_COMPARTIDO`, `03_PUBLICADO`, `04_ARCHIVO`.
- Cada archivo tiene contenido único y mtime fijo y distinto (hace ~30 días), para que
  tamaño + fecha identifique cada uno, como en una base real.
- Ruido que debe ignorarse: `~$Planta_N1.dwg`, `desktop.ini`.
- Espejo en modo `mirror`, exclusiones por defecto.

## Escenarios y resultados (2026-11-15)

| # | Cambio en origen | Resultado |
|---|---|---|
| 0 | Primer sync | 14 nuevos; ruido excluido. Segundo análisis: 0 cambios |
| 1 | Renombrar archivo, mover archivo, borrar uno, crear uno, modificar uno | 1 nuevo, 1 modificado, 2 movidos sin copiar, 1 borrado. Versión vieja y borrado van a `_archivo/<fecha>/` |
| 2 | Renombrar carpetas completas (`01_WIP` → `01_WIP_2026`, `Planos` → `Planos_Emitidos`) | 7 movidos, 0 bytes copiados (22 MB ahorrados) |
| 3 | Dos archivos gemelos (mismo tamaño y mtime), luego renombrar ambos | Ambiguo: no adivina. 2 nuevos + 2 archivados |
| 3 | Cambiar solo mayúsculas (`LEEME.txt` → `leeme.TXT`) | Sin cambios; el destino conserva el nombre antiguo |

## Hallazgos

- Cambio solo de mayúsculas no se propaga (comparación por `rel.lower()`). Aceptable en Windows; decisión pendiente.
- Modificado + cancelado o con error de copia: la versión vieja ya fue a `_archivo/` y la nueva aún no llegó, así que
  el archivo falta en `destino` hasta el siguiente sync (que lo recupera como «nuevo»). Nada se pierde, pero hay una
  ventana. Mejora posible: copiar a `.archive-tmp` primero y archivar la vieja justo antes del `os.replace`.

## Casos extremos (`stress`, 2026-11-15)

| Caso | Resultado |
|---|---|
| A Origen desconectado | `SyncError: Origen no disponible`, no analiza |
| B Origen vacío | `SyncError: El origen está vacío` |
| C 6 de 14 a archivo (43 %) | Plan marca 6; la UI pide confirmación extra (>30 %). Los 6 quedan en `_archivo/` |
| D Cancelar tras 5 pasos | `cancelled=True`, sin `.archive-tmp` sueltos; re-sync converge a 0 pendientes |
| E Ruta de 323 caracteres | Copiada sin error (prefijo `\?\`) |
| F Archivo bloqueado en origen | 13 copiados, 1 error legible, sin temporales; el resto sigue |
| G Subcarpeta sin permiso de lectura | `scan_errors=1`, `kept=2`, `deleted=0`: no archiva lo de esa carpeta |

No cubierto: Google Drive real, volúmenes grandes, disco lleno a mitad.
