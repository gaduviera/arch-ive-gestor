# Arch-Ive — Sync engine con detección de cambios

Fecha: 2026-11-09 (rev. 2026-11-15: espejos fijables) · Estado: pendiente de revisión del spec

## Propósito

Arch-Ive es un **copiador de archivos entre carpetas** para bases de carpetas masivas
(ej. CDE de ~800 GB en Google Drive Desktop → HDD externo). En una base viva los
archivos se crean, modifican, **mueven, renombran y borran**. Cada corrida debe
dejar el destino igual al origen sin recopiar lo que solo cambió de lugar y sin
perder nunca nada.

## Problema con el motor actual

`robocopy /E /MAXAGE:N /XO` solo copia nuevos/modificados de los últimos N días:

- Movido/renombrado → se recopia entero; la copia vieja queda huérfana en destino.
- Borrado en origen → queda para siempre en destino, sin aviso.
- Archivo viejo movido → `/MAXAGE` ni lo ve.

Además la pestaña Reportes siempre está vacía: `BackupHistoryManager.append_event`
nunca se llama desde la UI.

## Decisiones

| Tema | Decisión |
|---|---|
| Detección | Comparar árbol origen ↔ árbol destino en cada corrida, **sin estado** (sin manifest). |
| Borrados en origen | **Archivar** en `destino/_archivo/<YYYY-MM-DD>/<ruta relativa>`. |
| Modificados | **Archivar versión anterior** igual que borrados, luego copiar la nueva. |
| Unidad de trabajo | **Espejo**: par origen→destino con nombre, modo y exclusiones. Lista plana; cada espejo se puede **fijar**. Reemplaza "perfil" (decisión 2026-11-15). |
| Modos por espejo | **Espejo**: refleja borrados/modificados archivando en `_archivo/`. **Solo agregar**: copia nuevos/modificados (versión vieja igual se archiva), movidos se aplican, pero nunca archiva huérfanos sin pareja. |
| Lote | **Analizar fijados**: analiza todos los espejos fijados, una confirmación, ejecución en secuencia. |
| Motor de copia | `shutil.copy2` (preserva mtime), escritura a `.tmp` + rename. Robocopy se elimina. |
| Selector "últimos N días" | Se elimina: la comparación completa lo vuelve innecesario y escondía movidos. |
| Dirección | Unidireccional origen → destino. |

## Flujo

```
Espejo(s) → Escanear (origen + destino) → Planificar → Vista previa → Ejecutar → Historial + log
```

En lote ("Analizar fijados") el flujo corre por cada espejo fijado; la vista previa
muestra una fila por espejo con sus conteos y totales, y "Sincronizar todos" ejecuta
en secuencia. Un espejo con error de validación (origen inaccesible, etc.) se marca y
se salta; no frena a los demás.

### Escaneo

`os.scandir` recursivo en cada lado → `{ruta_relativa: (size, mtime_ns)}`.
Solo metadatos; en Google Drive Desktop no fuerza descarga.
Se ignoran: `_archivo/` en destino y las exclusiones del espejo.

Exclusiones por defecto (editables): `~$*`, `*.tmp`, `desktop.ini`, `Thumbs.db`, `.~lock*`.
Coincidencia con `fnmatch` sobre el nombre del archivo, sin distinguir mayúsculas.

### Clasificación (planificador)

Rutas comparadas en minúsculas (Windows no distingue mayúsculas).
Dos archivos son "iguales" si `size` coincide y `|mtime_a - mtime_b| <= 2 s`
(tolerancia FAT/exFAT).

1. **IGUAL**: ruta en ambos, igual → nada.
2. **MODIFICADO**: ruta en ambos, distinto → archivar destino + copiar.
3. Faltantes = en origen, no en destino. Huérfanos = en destino, no en origen.
4. **MOVIDO**: faltante F y huérfano H con mismo `(size, mtime)`. Si la clave
   `(size, mtime redondeado)` tiene exactamente un faltante y un huérfano → mover H→F
   dentro del destino. Si hay varios candidatos → no se adivina: F va a NUEVO y H a BORRADO.
   Renombrar es un caso de MOVIDO.
5. **NUEVO**: faltante sin pareja → copiar.
6. **BORRADO**: huérfano sin pareja → archivar (modo Espejo) o se deja en su lugar
   y solo se reporta (modo Solo agregar).

### Ejecución

Orden: movidos → archivados (borrados + versiones de modificados) → copias.
Mover primero libera las rutas y evita copiar lo que ya está.

- Copia: `shutil.copy2` a `<dest>.archive-tmp`, luego `os.replace` → nunca queda un archivo a medias.
- Archivar: `os.replace` hacia `_archivo/<fecha>/<ruta>`; si existe, sufijo `__1`, `__2`…
- Carpetas vacías que quedan en destino tras mover/archivar se eliminan
  (solo si están vacías).
- Cancelable entre archivos. Progreso por archivo y bytes.

## Seguridad y errores

- **Nunca se borra un archivo**: todo lo que sale del destino va a `_archivo/`.
- Origen inaccesible o vacío → abortar antes de planificar (evita marcar todo como borrado).
- Plan que archiva > 30 % de los archivos del destino → confirmación extra en la UI.
- Espacio libre del destino < bytes a copiar → no ejecuta.
- Error por archivo (bloqueado, sin permiso, ruta larga) → se registra, se sigue; resumen al final.
- Origen y destino iguales o anidados → rechazado al validar el espejo.
- Validación entre espejos: un destino dentro de otro destino (o igual) → rechazado;
  dos espejos con el mismo origen → aviso, se permite.

## Organización del repo

Layout consolidado (2026-11-09): la carpeta exterior es la raíz, con historial git
completo; remote `origin` = `github.com/gaduviera/arch-ive-gestor`.

```
main.py
core/                 # lógica pura, sin tkinter
  paths.py            # %APPDATA%\Arch-Ive
  mirrors.py          # espejos (CRUD, fijar, validación) + migración de config.json viejo
  sync.py             # escanear + planificar
  executor.py         # aplicar plan
  history.py          # ex reports_engine.py (historial + cálculos)
  duplicates.py       # ex duplicate_finder.py
  exporters.py        # ex export_csv/json/pdf
ui/
  app.py              # ventana + pestañas (ex ui.py)
  sync_tab.py         # nueva: lista de espejos, analizar, vista previa, ejecutar
  duplicates_tab.py
  reports_tab.py
  widgets.py          # heatmap, comparación, BarChart (ex reports_ui + chart_canvas)
  theme.py
tests/
```

Se eliminan: `backup_engine.py`, `components/frost_card.py`, `glass_button.py`,
`glass_input.py`, `LineChart` y sus tests (sin uso en la app), `config.json` del repo
(es dato de usuario, ya ignorado).

## Datos de usuario

`%APPDATA%\Arch-Ive\mirrors.json`:

```json
{"selected": "CDE completo",
 "mirrors": [{"name": "CDE completo", "source": "...", "dest": "...",
              "mode": "mirror",
              "pinned": true,
              "exclude": ["~$*", "*.tmp", "desktop.ini", "Thumbs.db", ".~lock*"],
              "last_run": null,
              "last_summary": null}]}
```

`mode`: `"mirror"` (Espejo) | `"add_only"` (Solo agregar).
`last_summary`: conteos del último análisis/ejecución, para mostrar estado en la lista.

Migración: si existe `config.json` viejo y no `mirrors.json`, se crea el espejo
"Principal" (modo Espejo, fijado) con `source_path`/`dest_path`.

Historial (`logs/backup_history.json`), un evento por espejo ejecutado:
`mirror, mode, new, modified, moved, archived, errors, bytes_copied, duration_s`.

## UI — pestaña Sincronizar

Layout de dos columnas.

**Izquierda — lista de espejos.** Fijados arriba (icono pin), luego no fijados.
Cada fila: nombre + modo + estado ("hace 6 días", "3 cambios pendientes", "nunca",
"origen no disponible"). Clic selecciona. Botones arriba: **Nuevo espejo**, **Analizar fijados**.

**Derecha — espejo seleccionado.**
- Nombre, badge de modo, origen ↓ destino, exclusiones.
- Tras analizar: tarjetas Nuevos / Modificados / Movidos / A archivo, GB a copiar y
  GB ahorrados por movidos.
- Botones: **Analizar**, **Ver detalle** (lista filtrable por tipo), **Sincronizar**
  (solo con plan vigente), **Editar**, **Abrir archivo** (`destino/_archivo/` en Explorer).

**Diálogo de espejo** (nuevo/editar): nombre, origen, destino (con "Explorar…"),
modo (Espejo / Solo agregar), fijar (sí/no), exclusiones (una por línea). Eliminar
un espejo borra solo su configuración, nunca archivos.

**Vista de lote** (tras "Analizar fijados"): una fila por espejo con conteos y estado,
total general, botón **Sincronizar todos**; progreso indica espejo actual y archivo.

## Tests (pytest, carpetas temporales reales)

- Planificador: nuevo, modificado, movido, renombrado, borrado, movido ambiguo,
  exclusiones, tolerancia de mtime, mayúsculas.
- Ejecutor: aplica plan; segunda corrida = plan vacío; archivado con sufijo en colisión;
  carpetas vacías limpiadas.
- Espejos: CRUD, fijar, migración de config viejo, validación de rutas anidadas y
  destinos solapados entre espejos.
- Modo Solo agregar: huérfanos sin pareja no se archivan.
- Lote: un espejo inválido se salta sin frenar a los demás.
- Historial: evento registrado tras ejecutar.
- Se conservan tests de historial/reportes, exportadores, theme y BarChart.

## Fuera de alcance (YAGNI)

Sincronización bidireccional, programación automática, purga automática de `_archivo/`,
hashing de contenido, compresión/cifrado. Se agregan cuando haya necesidad real.
