# Duplicados v2 — Design Spec
**Fecha:** 2026-04-08  
**Archivo:** `symetra_backup/duplicates_tab.py`

---

## Bugs a corregir

### Scroll excesivo
El `scrollregion` del canvas se actualiza antes de que los widgets terminen de renderizarse. Fix: llamar `update_idletasks()` antes de recalcular el bbox.

---

## Acordeón desplegable

Cada grupo de duplicados pasa de mostrarse siempre expandido a tener un header clickeable.

**Header (colapsado):**
```
▶  documento.pdf  |  2.3 MB  |  3 copias
```

**Header (expandido):**
```
▼  documento.pdf  |  2.3 MB  |  3 copias
   ☐  documento.pdf   C:\Proyectos\CDE\carpeta\          [Abrir en Explorer]
   ☐  documento.pdf   D:\Backup\2024\carpeta\            [Abrir en Explorer]
   ☐  documento.pdf   G:\HDD\Archivos\carpeta\           [Abrir en Explorer]
                                          [Eliminar seleccionados]
```

**Reglas:**
- Click en header toggle expand/collapse del grupo
- Checkbox por cada fila de ruta
- Botón "Eliminar seleccionados" visible solo si ≥1 checkbox marcado
- Confirmación antes de borrar: `"¿Eliminar X archivo(s)? Esta acción no se puede deshacer."`
- Tras borrar: quitar filas eliminadas del grupo; si queda 1 copia, eliminar el grupo entero
- Botón "Abrir en Explorer" abre el Explorer con el archivo seleccionado (`explorer /select,<path>`)

---

## Toolbar superior

```
[ Colapsar todos ]  [ Expandir todos ]    Ordenar: [ Tamaño ▼ ] [ Copias ▼ ]
Espacio recuperable: 1.24 GB   |   8 grupos de duplicados
```

- **Colapsar todos / Expandir todos:** colapsa o expande todos los grupos de una vez
- **Ordenar por tamaño:** ordena grupos de mayor a menor tamaño de archivo
- **Ordenar por cantidad de copias:** ordena de mayor a menor cantidad de copias
- **Espacio recuperable:** suma del `size * (n_copias - 1)` de cada grupo (lo que se ahorraría borrando todas las copias extra)

---

## Archivos a modificar

| Archivo | Cambio |
|---|---|
| `duplicates_tab.py` | Reescribir `_render_results`, agregar toolbar, fix scroll |
| `duplicate_finder.py` | Sin cambios |

---

## Branding
Mismo esquema existente: `#111111 / #C6A85E / #1A1A1A / #F5F5F5`
