<img width="1774" height="887" alt="image" src="https://github.com/user-attachments/assets/917a4376-3ca1-4790-abb5-9cddc2d619d2" />
# Arch-Ive by SYMETRA — Gestor de Copias de Seguridad | Backup Manager

[![Python](https://img.shields.io/badge/Python-3.11+-3776ab?logo=python)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![GitHub](https://img.shields.io/badge/GitHub-gaduviera%2Farch--ive--gestor-181717?logo=github)](https://github.com/gaduviera/arch-ive-gestor)

**Arch-Ive by SYMETRA** es una aplicación de escritorio para Windows que simplifica y potencia tus tareas de respaldo de archivos. Utiliza el motor nativo Robocopy, ofrece un diseño moderno con efectos glassmorphism y una pestaña completa de análisis e informes.

***Arch-Ive by SYMETRA** is a Windows desktop application that simplifies and enhances your file backup tasks. It leverages the native Robocopy engine, features a modern glassmorphism design, and includes a full reports & analytics tab.*

---

## ✨ Características | Features

- **Copias de seguridad incrementales** via Robocopy con rangos seleccionables: 7 / 15 / 30 / 60 días
- **Modo Dry Run** — vista previa antes de ejecutar cualquier operación
- **Registro en tiempo real** del progreso de cada respaldo
- **Configuración persistente** — guarda rutas y fecha del último respaldo
- **Diseño glassmorphism** — paneles translúcidos con efectos de cristal esmerilado y acentos dorados
- **Gráficos integrados** — BarChart y LineChart con gradientes para visualizar tendencias
- **Detector de duplicados** — por nombre y tamaño idénticos, con grupos colapsables y checkbox
- **Eliminación segura** de duplicados con confirmación previa
- **Calculadora de espacio recuperable**

---

## 📊 Informes y Analíticas | Reports & Analytics

La pestaña **Reportes** ofrece una visión completa del historial de respaldos:

- **Mapa de calor mensual** — visualiza qué días del mes se hicieron respaldos
- **Totales anuales** — gráfico de barras con conteo por mes
- **Comparación de períodos** — compara dos rangos de fechas con delta porcentual
- **Exportación en PDF, CSV y JSON** — descarga el historial completo en el formato que prefieras

---

## 🛠️ Tech Stack

| Componente | Detalle |
|-----------|---------|
| **Backend** | Python 3.11+ |
| **UI** | tkinter (nativa) + Pillow (efectos glassmorphism) |
| **Backup Engine** | Robocopy (incluido en Windows) |
| **Reports** | reportlab (PDF, opcional) |
| **Packaging** | PyInstaller |

---

## 📦 Instalación | Installation

### Requisitos | Requirements
- Windows 10 / 11
- Python 3.11+
- Robocopy (incluido en Windows por defecto)

### Quick Start

```bash
# Clonar el repositorio
git clone https://github.com/gaduviera/arch-ive-gestor.git
cd arch-ive-gestor

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar la aplicación
python main.py
```

### Compilar ejecutable | Build Executable

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name ArchIve main.py
# Resultado: dist/ArchIve.exe
```

---

## 📂 Estructura del Proyecto | Project Structure

```
arch-ive-gestor/
├── main.py                # Punto de entrada
├── ui.py                  # UI principal (tkinter)
├── backup_engine.py       # Wrapper de Robocopy
├── duplicate_finder.py    # Lógica de detección de duplicados
├── duplicates_tab.py      # Pestaña de duplicados
├── config.py              # Gestión de configuración
├── theme.py               # Paleta y utilidades de color
├── reports_engine.py      # Motor de historial e informes
├── reports_tab.py         # Pestaña de Reportes
├── reports_ui.py          # Componentes visuales de informes
├── export_csv.py          # Exportador CSV
├── export_json.py         # Exportador JSON
├── export_pdf.py          # Exportador PDF
├── requirements.txt
├── assets/
│   └── mesh_grain.png
├── components/
│   ├── frost_card.py      # Panel glassmorphism
│   ├── glass_button.py    # Botón con gradiente
│   ├── glass_input.py     # Input estilizado
│   └── chart_canvas.py    # Gráficos BarChart / LineChart
├── tests/                 # 78 tests unitarios
└── logs/                  # Logs de runtime (gitignored)
```

---

Made with ❤️ by [Gabriel Duarte Viera](https://github.com/gaduviera)
