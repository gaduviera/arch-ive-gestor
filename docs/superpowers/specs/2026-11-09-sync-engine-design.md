# Arch-Ive — Sync engine con detección de cambios

Fecha: 2026-11-09 · Estado: aprobado en brainstorming, pendiente de revisión del spec

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
| Perfiles | **Varios perfiles** con nombre: origen, destino, exclusiones. |
| Motor de copia | `shutil.copy2` (preserva mtime), escritura a `.tmp` + rename. Robocopy se elimina. |
| Selector "últimos N días" | Se elimina: la comparación completa lo vuelve innecesario y escondía movidos. |
| Dirección | Unidireccional origen → destino. |

## Flujo

```
Perfil → Escanear (origen + destino) → Planificar → Vista previa → Ejecutar → Historial + log
```

### Escaneo

`os.scandir` recursivo en cada lado → `{ruta_relativa: (size, mtime_ns)}`.
Solo metadatos; en Google Drive Desktop no fuerza descarga.
Se ignoran: `_archivo/` en destino y las exclusiones del perfil.

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
6. **BORRADO**: huérfano sin pareja → archivar.

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
- Origen y destino iguales o anidados → rechazado al validar el perfil.

## Organización del repo

Layout consolidado (2026-11-09): la carpeta exterior es la raíz, con historial git
completo; remote `origin` = `github.com/gaduviera/arch-ive-gestor`.

```
main.py
core/                 # lógica pura, sin tkinter
  paths.py            # %APPDATA%\Arch-Ive
  profiles.py         # perfiles + migración de config.json viejo → perfil "Principal"
  sync.py             # escanear + planificar
  executor.py         # aplicar plan
  history.py          # ex reports_engine.py (historial + cálculos)
  duplicates.py       # ex duplicate_finder.py
  exporters.py        # ex export_csv/json/pdf
ui/
  app.py              # ventana + pestañas (ex ui.py)
  sync_tab.py         # nueva: perfiles, escanear, vista previa, ejecutar
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

`%APPDATA%\Arch-Ive\profiles.json`:

```json
{"active": "Principal",
 "profiles": [{"name": "Principal", "source": "...", "dest": "...",
               "exclude": ["~$*", "*.tmp", "desktop.ini", "Thumbs.db", ".~lock*"],
               "last_run": null}]}
```

Migración: si existe `config.json` viejo y no `profiles.json`, se crea el perfil
"Principal" con `source_path`/`dest_path`.

Historial (`logs/backup_history.json`), un evento por ejecución:
`profile, new, modified, moved, archived, errors, bytes_copied, duration_s, dry_run=false`.

## UI — pestaña Sincronizar

- Selector de perfil + Nuevo / Editar / Eliminar perfil (diálogo: nombre, origen, destino, exclusiones).
- Botón **Analizar** → resumen por tipo (conteo + GB) y lista filtrable por tipo.
- Botón **Sincronizar** (habilitado solo con plan vigente) → progreso + log.
- Botón **Abrir archivo** → abre `destino/_archivo/` en Explorer.

## Tests (pytest, carpetas temporales reales)

- Planificador: nuevo, modificado, movido, renombrado, borrado, movido ambiguo,
  exclusiones, tolerancia de mtime, mayúsculas.
- Ejecutor: aplica plan; segunda corrida = plan vacío; archivado con sufijo en colisión;
  carpetas vacías limpiadas.
- Perfiles: CRUD + migración de config viejo + validación de rutas anidadas.
- Historial: evento registrado tras ejecutar.
- Se conservan tests de historial/reportes, exportadores, theme y BarChart.

## Fuera de alcance (YAGNI)

Sincronización bidireccional, programación automática, purga automática de `_archivo/`,
hashing de contenido, compresión/cifrado. Se agregan cuando haya necesidad real.
