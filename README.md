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

## 🤝 Contributors

[![All Contributors](https://img.shields.io/badge/all_contributors-3-orange.svg?style=flat-square)](#contributors)

Thanks to these amazing contributors:

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tbody>
    <tr>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/weedorpy"><img src="https://avatars.githubusercontent.com/u/weedorpy?s=100" width="100px;" alt="Gabriel Duarte Viera"/><br /><sub><b>Gabriel Duarte Viera</b></sub></a><br /><a href="#code-weedorpy" title="Code">💻</a> <a href="#design-weedorpy" title="Design">🎨</a> <a href="#ideas-weedorpy" title="Ideas, Planning, & Feedback">🤔</a> <a href="#maintenance-weedorpy" title="Maintenance">🚧</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://claude.ai"><img src="https://www.anthropic.com/_next/image?url=%2F_next%2Fstatic%2Fmedia%2Fclaude_app_icon.a82a8ab9.png&w=96&q=75" width="100px;" alt="Claude"/><br /><sub><b>Claude</b></sub></a><br /><a href="#code-claude" title="Code">💻</a> <a href="#design-claude" title="Design">🎨</a> <a href="#ideas-claude" title="Ideas, Planning, & Feedback">🤔</a> <a href="#review-claude" title="Reviewed Pull Requests">👀</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://openai.com/blog/openai-codex/"><img src="https://user-images.githubusercontent.com/10909/97088124-d8a3be00-1652-11eb-8c64-35b11070b5f0.png" width="100px;" alt="Codex"/><br /><sub><b>Codex</b></sub></a><br /><a href="#code-codex" title="Code">💻</a> <a href="#ideas-codex" title="Ideas, Planning, & Feedback">🤔</a></td>
    </tr>
  </tbody>
</table>

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

<!-- ALL-CONTRIBUTORS-LIST:END -->

**Legends:**
- 💻 Code
- 🎨 Design
- 🤔 Ideas, Planning, & Feedback
- 👀 Code Review
- 🚧 Maintenance

---

Made with ❤️ by Gabriel Duarte Viera
