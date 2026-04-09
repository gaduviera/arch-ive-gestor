# Arch-Ive by SYMETRA

[![GitHub](https://img.shields.io/badge/GitHub-weedorpy%2Farch--ive--gestor-181717?logo=github)](https://github.com/weedorpy/arch-ive-gestor)
[![Python](https://img.shields.io/badge/Python-3.11+-3776ab?logo=python)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

Herramienta profesional para respaldo incremental y detección de archivos duplicados en entornos CDE.  
*Professional backup and duplicate file detection tool for CDE environments.*

## Espanol
**Arch-Ive by SYMETRA**  
Herramienta para respaldo incremental de entornos CDE y deteccion de archivos duplicados, disenada para ofrecer control operativo, visibilidad del proceso y una experiencia clara para el usuario.

### Caracteristicas
- Respaldo incremental mediante Robocopy con rangos de dias seleccionables: 7 / 15 / 30 / 60
- Seleccion de carpetas de origen y destino sin letras de unidad fijas
- Vista previa `Dry Run` antes de ejecutar el proceso
- Registro de progreso en tiempo real
- Configuracion persistente que guarda las ultimas rutas y la fecha del ultimo respaldo
- Buscador de archivos duplicados por mismo nombre y mismo tamano
- Grupos tipo acordeon colapsables con seleccion mediante casillas
- Eliminacion de duplicados con confirmacion
- Apertura de la ubicacion del archivo en el Explorador de Windows
- Calculadora de espacio recuperable
- Ordenacion por tamano o por cantidad de copias
- Identidad visual oscura de SYMETRA: Carbon Black + Gold

### Stack Tecnologico
- Python
- tkinter
- Robocopy
- PyInstaller

### Como ejecutar
```bash
cd symetra_backup
python main.py
```

### Como generar el `.exe`
```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name ArchIve_SYMETRA main.py
```

## English
**Arch-Ive by SYMETRA**  
Tool for incremental CDE backup and duplicate file detection, built to provide operational control, process visibility, and a clean desktop workflow.

### Features
- Incremental backup via Robocopy with selectable day ranges: 7 / 15 / 30 / 60
- Source and destination folder selection with no fixed drive letters
- `Dry Run` preview before execution
- Real-time progress log
- Persistent configuration that saves the last paths and backup date
- Duplicate file finder based on same name and same size
- Collapsible accordion groups with checkbox selection
- Duplicate deletion with confirmation
- Open file location in Explorer
- Recoverable space calculator
- Sort by size or by copy count
- SYMETRA dark branding: Carbon Black + Gold

### Tech Stack
- Python
- tkinter
- Robocopy
- PyInstaller

### How to Run
```bash
cd symetra_backup
python main.py
```

### How to Build the `.exe`
```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name ArchIve_SYMETRA main.py
```

## Portugues
**Arch-Ive by SYMETRA**  
Ferramenta para backup incremental de ambientes CDE e localizacao de arquivos duplicados, desenvolvida para oferecer controle operacional, visibilidade do processo e uma experiencia de uso objetiva.

### Recursos
- Backup incremental via Robocopy com faixas de dias selecionaveis: 7 / 15 / 30 / 60
- Selecao de pastas de origem e destino sem letras de unidade fixas
- Pre-visualizacao em `Dry Run` antes da execucao
- Log de progresso em tempo real
- Configuracao persistente que salva os ultimos caminhos e a data do ultimo backup
- Localizador de arquivos duplicados por mesmo nome e mesmo tamanho
- Grupos em acordeao recolhiveis com selecao por checkbox
- Exclusao de duplicados com confirmacao
- Abertura da localizacao do arquivo no Explorer
- Calculadora de espaco recuperavel
- Ordenacao por tamanho ou quantidade de copias
- Identidade visual escura da SYMETRA: Carbon Black + Gold

### Stack Tecnologica
- Python
- tkinter
- Robocopy
- PyInstaller

### Como executar
```bash
cd symetra_backup
python main.py
```

### Como gerar o `.exe`
```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name ArchIve_SYMETRA main.py
```

## Setup & Installation

### Requirements
- Python 3.11+
- Robocopy (Windows native)
- tkinter (included with Python)

### Quick Start
```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

### Build Executable
```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name ArchIve_SYMETRA main.py
# Output: dist/ArchIve_SYMETRA.exe
```

---

## Contributors

**Made by:** Gabriel Duarte Viera

**With AI Assistance:**
- [Claude](https://claude.ai/) (Anthropic) — Architecture, feature design, debugging
- [Codex](https://openai.com/blog/openai-codex/) — Code generation and optimization

---

Created with ❤️ by Gabriel Duarte Viera
