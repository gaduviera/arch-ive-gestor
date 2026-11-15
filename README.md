<img width="1774" height="887" alt="image" src="https://github.com/user-attachments/assets/917a4376-3ca1-4790-abb5-9cddc2d619d2" />
# Arch-Ive by SYMETRA — Espejos de carpetas | Folder Mirrors

[![Python](https://img.shields.io/badge/Python-3.11+-3776ab?logo=python)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![GitHub](https://img.shields.io/badge/GitHub-gaduviera%2Farch--ive--gestor-181717?logo=github)](https://github.com/gaduviera/arch-ive-gestor)

**Arch-Ive** copia carpetas en otras carpetas y las mantiene al día, pensado para bases
grandes y vivas (por ejemplo un CDE de cientos de GB en Google Drive → disco externo).
Cada par origen → destino es un **espejo**. En cada corrida compara las dos carpetas y
detecta qué es nuevo, qué cambió, qué se **movió o renombró** y qué se borró. Nunca pierde
nada: lo que sale del destino va a `_archivo/<fecha>/`.

*Arch-Ive keeps folder pairs in sync on Windows. It detects new, modified, moved/renamed
and deleted files, moves instead of re-copying, and archives instead of deleting.*

---

## Cómo se usa | How it works

1. **Nuevo espejo** → nombre, carpeta origen, carpeta destino, modo.
2. **Analizar** → ves cuántos archivos son nuevos, modificados, movidos o van a archivo,
   y cuántos GB se copian. **Ver detalle** lista cada archivo.
3. **Sincronizar** → aplica el plan. Confirma antes, con avisos si algo parece raro.
4. Repite para cada par. Los espejos **fijados** se analizan y sincronizan juntos con
   **Analizar fijados**.

| Qué pasó en el origen | Qué hace el destino |
|---|---|
| Archivo nuevo | Se copia |
| Archivo modificado | La versión vieja va a `_archivo/<fecha>/`, se copia la nueva |
| Archivo movido o renombrado | Se mueve dentro del destino, **sin volver a copiarlo** |
| Archivo borrado | Modo *Espejo*: va a `_archivo/<fecha>/`. Modo *Solo agregar*: se queda |

### Modos

- **Espejo** — el destino queda igual al origen; todo lo que sale va a `_archivo/`.
- **Solo agregar** — copia nuevos y modificados, nunca saca del destino lo borrado en el origen.

### Protecciones

- Origen desconectado o vacío → no se analiza (no marca todo como borrado).
- Carpetas del origen sin permiso de lectura → sus archivos en destino no se tocan.
- Más del 30 % del destino iría a `_archivo/` → confirmación extra.
- Falta espacio en destino → no arranca.
- Copias a archivo temporal + renombrado: un corte nunca deja archivos a medias.
- Un movido se reconoce por tamaño + fecha de modificación (±2 s). Si hay ambigüedad,
  no adivina: copia y archiva.

### Otras pestañas

- **Duplicados** — busca archivos con mismo nombre y tamaño en una carpeta.
- **Reportes** — historial de sincronizaciones: actividad mensual, totales, export CSV/JSON/PDF.

---

## Instalación | Installation

Requisitos: Windows 10/11, Python 3.11+. Sin dependencias externas para la app
(`reportlab` opcional para exportar PDF).

```bash
git clone https://github.com/gaduviera/arch-ive-gestor.git
cd arch-ive-gestor
python main.py
```

Tests:

```bash
pip install pytest
python -m pytest
```

Ejecutable:

```bash
pip install pyinstaller
pyinstaller ArchIve.spec --noconfirm
```

Datos de usuario en `%APPDATA%\Arch-Ive\` (`mirrors.json`, `logs/`).

---

## Estructura | Project Structure

```
arch-ive-gestor/
├── main.py              # Punto de entrada
├── core/                # Lógica pura (sin tkinter)
│   ├── sync.py          # Escanear origen/destino y planificar cambios
│   ├── executor.py      # Aplicar el plan: mover, archivar, copiar
│   ├── mirrors.py       # Espejos: guardar, validar, fijar
│   ├── history.py       # Historial y cálculos de reportes
│   ├── duplicates.py    # Detector de duplicados
│   ├── exporters.py     # CSV / JSON / PDF
│   └── paths.py         # Rutas en %APPDATA%\Arch-Ive
├── ui/                  # Interfaz tkinter
│   ├── app.py           # Ventana y pestañas
│   ├── sync_tab.py      # Pestaña Sincronizar + diálogos
│   ├── duplicates_tab.py
│   ├── reports_tab.py
│   ├── widgets.py       # Heatmap, comparación, gráfico de barras
│   └── theme.py         # Paleta SYMETRA
├── tests/
├── installer/           # Inno Setup
└── docs/                # Specs y planes
```

---

Made by [Gabriel Duarte Viera](https://github.com/gaduviera)
