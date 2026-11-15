
# Arch-Ive_by_SYMETRA — CDE Backup Tool (MVP)
## Planning.md

---

# 🎯 Objetivo

El objetivo es desarrollar una herramienta MVP local, simple y robusta, que permita realizar sincronizaciones incrementales inteligentes del Entorno Común de Datos (CDE) de la empresa, el cual actualmente se encuentra en Google Drive Desktop con aproximadamente 800 GB de información, partiendo de una estrategia en la que primero se realizará un backup completo inicial hacia un HDD externo de 1 TB y, a partir de ese punto, se utilizará la herramienta para ejecutar copias incrementales periódicas (cada 15, 20 o 30 días) que detecten únicamente archivos nuevos o modificados dentro de ese rango de tiempo, evitando así tener que volver a copiar toda la información y reduciendo significativamente el tiempo de transferencia, manteniendo siempre la misma estructura de carpetas para que los archivos se coloquen automáticamente en su ubicación correspondiente dentro del backup, sin depender de letras de disco fijas como E:, G: o D:, mediante una interfaz sencilla que permita seleccionar manualmente la carpeta raíz del CDE y la carpeta destino del backup, definir el rango de días a analizar y ejecutar la sincronización utilizando un motor robusto como Robocopy (o alternativa equivalente), garantizando eficiencia, estabilidad y escalabilidad, y con un frontend minimalista alineado al branding de SYMETRA (carbono oscuro y acentos dorados), con la intención de construir inicialmente una herramienta práctica de uso personal o interno que optimice la gestión de backups incrementales del CDE, evitando reprocesamientos innecesarios, minimizando tiempos de copia y estableciendo una rutina confiable de sincronización periódica.

Desarrollar una herramienta MVP para sincronización incremental del Entorno Común de Datos (CDE), permitiendo:

- Seleccionar carpeta origen (CDE)
- Seleccionar carpeta destino (Backup HDD)
- Copiar archivos nuevos o modificados
- Filtrar por últimos X días
- Mantener estructura de carpetas
- Ejecutar sincronización incremental rápida
- Interfaz simple y visual (branding SYMETRA)

---

# 🧠 Concepto Técnico

## Flujo Principal

1. Backup Full Inicial (Manual)
2. Sincronización Incremental (Script MVP)
3. Copia solo archivos:
   - Nuevos
   - Modificados
   - Últimos X días

---

# ⚙️ Arquitectura del MVP

```
UI (Python)
    ↓
Motor Sync (Robocopy)
    ↓
Destino HDD
```

---

# 🧩 Funcionalidades MVP

## Selección de Carpetas

- Botón seleccionar carpeta origen
- Botón seleccionar carpeta destino
- No depender de letras de disco (E:, G:, etc.)

---

## Sincronización Incremental

Debe:

- Detectar archivos nuevos
- Detectar archivos modificados
- Filtrar últimos X días
- Mantener estructura original

---

## Configuración de Días

Selector:

- 7 días
- 15 días
- 30 días
- 60 días

---

# 🎨 UI — Branding SYMETRA

## Estilo Visual

Colores:

- Carbon Black: #111111
- Gold Accent: #C6A85E
- Gray Dark: #1A1A1A
- White Soft: #F5F5F5

---

## Layout UI

```
----------------------------------
Arch-Ive_by_SYMETRA CDE Backup Tool
----------------------------------

[Seleccionar Carpeta CDE]

[Seleccionar Carpeta Backup]

Últimos días:
[ 30 ▼ ]

[ Ejecutar Backup ]

[ Barra de Progreso ]

----------------------------------
```

---

# 🏗️ Estructura Proyecto

```
symetra_backup/
│
├── main.py
├── ui.py
├── backup_engine.py
├── config.py
├── assets/
│   ├── logo.png
│
└── logs/
```

---

# ⚙️ Comando Motor (Robocopy)

Ejemplo:

```
robocopy origen destino /E /MAXAGE:30 /XO /MT:8
```

---

# 🧠 Lógica del Script

1. Seleccionar origen
2. Seleccionar destino
3. Leer días seleccionados
4. Ejecutar robocopy
5. Mostrar progreso
6. Generar log

---

# 🚀 Fase 1 — MVP

✔ UI simple  
✔ Selección carpetas  
✔ Sync incremental  
✔ Robocopy  

---

# 🚀 Fase 2 — Mejoras

✔ Guardar configuración  
✔ Auto detección HDD  
✔ Barra progreso avanzada  

---

# 🚀 Fase 3 — Profesional

✔ Backup automático  
✔ Versionado  
✔ Reportes  

---

# 🧠 Skills para IA Local

## Software Architect

Diseñar arquitectura modular

---

## Python Engineer

Construcción UI

---

## File Sync Engineer

Optimización copia archivos

---

## UI Designer

Diseño estilo SYMETRA

---

# 🎯 Prompt para IA Local

Actúa como ingeniero senior y crea una herramienta MVP en Python para sincronización incremental de un Entorno Común de Datos (CDE).

Debe:

- UI simple
- Selección carpetas
- Selector días
- Ejecutar Robocopy
- Estilo visual SYMETRA
- Código modular

---

# 📊 Objetivo Final

Herramienta local ligera para:

- Backup incremental
- Sincronización rápida
- Uso empresarial
- Escalable
