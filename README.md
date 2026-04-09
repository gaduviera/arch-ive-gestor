# Arch-Ive by SYMETRA

[![GitHub](https://img.shields.io/badge/GitHub-weedorpy%2Farch--ive--gestor-181717?logo=github)](https://github.com/weedorpy/arch-ive-gestor)
[![Python](https://img.shields.io/badge/Python-3.11+-3776ab?logo=python)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

Herramienta profesional para respaldo incremental y detección de archivos duplicados en entornos CDE.  
*Professional backup and duplicate file detection tool for CDE environments.*  
*Ferramenta para backup incremental de ambientes CDE e localização de arquivos duplicados.*

---

## ✨ Características | Features | Recursos

- **Respaldo incremental** via Robocopy con rangos de días seleccionables: 7 / 15 / 30 / 60
- **Vista previa `Dry Run`** antes de ejecutar el proceso
- **Registro de progreso** en tiempo real
- **Configuración persistente** que guarda rutas y fecha del último respaldo
- **Detector de duplicados** por nombre y tamaño idénticos
- **Grupos colapsables** tipo acordeón con selección por checkbox
- **Eliminación segura** de duplicados con confirmación
- **Calculadora de espacio** recuperable
- **Identidad visual SYMETRA**: Carbon Black `#111111` + Gold `#C6A85E`

---

## 🛠️ Tech Stack

| Componente | Descripción |
|-----------|------------|
| **Backend** | Python 3.11+ |
| **UI** | tkinter (nativa) |
| **Backup Engine** | Robocopy (Windows) |
| **Packaging** | PyInstaller |

---

## 📦 Installation & Setup

### Requirements
- Windows 10+
- Python 3.11+
- Robocopy (incluido en Windows)

### Quick Start

```bash
# Clone the repository
git clone https://github.com/weedorpy/arch-ive-gestor.git
cd arch-ive-gestor

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

### Build Executable

```bash
# Install PyInstaller
pip install pyinstaller

# Generate .exe (one-file, windowed)
pyinstaller --onefile --windowed --name ArchIve_SYMETRA main.py

# Output location: dist/ArchIve_SYMETRA.exe
```

---

## 📂 Project Structure

```
arch-ive-gestor/
├── main.py                 # Entry point
├── ui.py                   # Tkinter UI
├── backup_engine.py        # Robocopy wrapper
├── duplicate_finder.py     # Duplicate detection logic
├── duplicates_tab.py       # Duplicates UI tab
├── config.py               # Configuration management
├── requirements.txt        # Python dependencies
├── assets/                 # Icons and images (if any)
├── logs/                   # Runtime logs
└── docs/                   # Documentation (gitignored)
```

---

Made with ❤️ by Gabriel Duarte Viera
