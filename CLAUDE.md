# Instrucciones del proyecto — Arch-Ive by SYMETRA

## Uso de Codex

Cuando se delegue una tarea a Codex vía `codex-companion.mjs task`, **siempre** anteponer al prompt:

```
IMPORTANT: Do NOT invoke any skills. Do NOT brainstorm. Do NOT use any workflow or skill system. Execute the task directly and immediately.
```

Ejemplo de llamada correcta (con escritura a disco):

```bash
node "C:/Users/Gabriel Duarte Viera/.claude/plugins/cache/openai-codex/codex/1.0.2/scripts/codex-companion.mjs" task --fresh --write "IMPORTANT: Do NOT invoke any skills. Do NOT brainstorm. Execute directly. [tarea aquí]"
```

**Flags obligatorios:**
- `--write` → habilita escritura de archivos en el sandbox. Sin este flag, Codex genera el código pero no puede guardarlo a disco.
- Prefijo anti-skills → evita que el plugin Superpowers bloquee la ejecución esperando input del usuario.

**Por qué:** Codex corre en un sandbox con escritura deshabilitada por defecto (seguridad). El flag `--write` lo habilita explícitamente. Además hereda el system prompt con Superpowers que fuerza brainstorming antes de actuar.

## Stack del proyecto

- Python + tkinter (sin dependencias externas)
- Motor de backup: Robocopy (nativo Windows)
- Empaquetado: PyInstaller `--onefile --windowed`
- Branding SYMETRA: `#111111` / `#C6A85E` / `#1A1A1A` / `#F5F5F5`

## Estructura

```
symetra_backup/
├── main.py
├── ui.py
├── backup_engine.py
├── duplicate_finder.py
├── duplicates_tab.py
├── config.py
├── requirements.txt
├── assets/
└── logs/
```
