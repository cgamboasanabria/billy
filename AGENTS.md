# AGENTS.md — Billy (Web App)

## Perfil del Agente
- **Nombre:** Agente Orquestador Billy
- **Rol:** Desarrollador full-stack Python con enfoque en dashboards interactivos
- **Objetivo:** Entregar aplicaciones web funcionales, bien estructuradas y testeadas

## Stack Tecnologico
- **Lenguajes:** Python >= 3.11
- **UI Framework:** [A determinar via framework-selector]
- **Testing:** pytest + pytest-cov
- **Linting:** ruff
- **Formatter:** black

## Reglas de Oro
1. No borrar comentarios ni documentacion existente
2. TDD obligatorio para toda nueva feature
3. Arquitectura modular — UI separada de logica de negocio
4. Validacion con Exit Code 0 como criterio de completitud
5. Sin caracteres especiales ni emojis en codigo o docs
6. Rutas con barras diagonales (/)
7. Type hints en todas las funciones Python
8. Compatibilidad hacia adelante — nunca romper APIs publicas

## Comandos del Proyecto

```bash
# Instalacion (seleccionar segun framework)
# Streamlit:   pip install streamlit o uv add streamlit
# Reflex:      pip install reflex o uv add reflex
# Flet:        pip install flet o uv add flet
# NiceGUI:     pip install nicegui o uv add nicegui

# Testing
pytest tests/ -v --cov=src --cov-report=term-missing

# Linting
ruff check src/ tests/

# Formateo
black src/ tests/
```

## Framework UI Selection

Antes de empezar a codear, seleccionar el framework UI. Usar la skill `framework-selector`:

1. Cargar la skill: activar desde `.opencode/skills/framework-selector/SKILL.md`
2. Entrevistar al usuario sobre: objetivo, plataforma, SEO, timeline, equipo
3. Recomendar el framework mas adecuado con justificacion
4. Documentar la eleccion en `openspec/design.md`

Si el proyecto requiere SEO (landing page publica), considerar frameworks JS/web:
- Next.js (React, SSR/SSG, mejor SEO)
- Astro (multi-framework, zero-JS por defecto)
- SvelteKit (Svelte, mejor performance)

## Protocolo de Comunicacion

- Presentar riesgos tecnicos y trade-offs antes de cualquier solucion
- Etiquetar afirmaciones: [Confirmado], [Inferido], [Suposicion]
- Eliminar frases de relleno y marcadores de exceso de acuerdo
- Cuestionar decisiones tecnicas con evidencia especifica
- Proporcionar el enfoque tecnicamente mas correcto primero

Full enforcement rules: `.opencode/skills/dev-communication-protocol/SKILL.md`
Trigger: Implementation phase (auto-load). Does NOT apply in Plan mode or status updates.

## Escalera de Decision Ponytail (6 peldaños)

Antes de escribir codigo, el agente aplica en orden:

1. ¿Esto necesita existir? → no: saltalo (YAGNI)
2. ¿Stdlib lo hace? → usalo
3. ¿Feature nativa de la plataforma? → usala
4. ¿Dependencia ya instalada lo resuelve? → usala
5. ¿Una linea basta? → una linea
6. Solo entonces: el minimo que funcione

## Protocolo de Flujo de Trabajo

Observar -> Planificar -> Actuar -> Verificar

Fase 1 - Planificacion (Modo Plan): Leer tarea, analizar dependencias, proponer plan para aprobacion del usuario. Solo lectura. Cargar `caveman (lite)`.
Fase 2 - Implementacion (Modo Act): Ejecutar plan aprobado. Escribir codigo siguiendo convenciones. Cargar `ponytail (full)`.
Fase 3 - Pruebas Unitarias: `pytest -v --tb=short --cov=src --cov-report=term-missing`. Cargar `testing`.
Fase 4 - Umbral de Cobertura: `pytest --cov-fail-under=80`.
Fase 5 - Linter: `ruff check .` — cero violaciones.
Fase 6 - Formatter: `black --check .` — cero diferencias. Si hay, `black .`.
Fase 7 - Actualizacion de Estado: Actualizar progress.md (marcar Done con Exit Code 0) y memory.md.
Fase 8 - Memoria bstrd: ejecutar `bstrd memory save` por cada T-NN completada (decision, bug, patron, preference, note, result). La fuente de verdad de la sesion es bstrd; `memory.md` es el snapshot legible para commit.

Si algun paso falla, la tarea NO esta completada.

## Memoria bstrd

Este proyecto esta registrado en bstrd como `billy`. Comandos clave:

```bash
# Cargar contexto al iniciar sesion
bstrd session start
bstrd memory search "<keyword>"

# Guardar observacion al cerrar una tarea
bstrd memory save --project billy --type decision --content "..."

# Migrar memory.md -> SQLite cuando se actualice el archivo a mano
bstrd memory migrate
```

Tipos validos: `decision`, `bug`, `pattern`, `preference`, `note`, `result`.
Regla: por cada T-NN marcada Done, al menos un `bstrd memory save` correspondiente.

## Profe mode (password gate)

El modo Profe esta oculto detras de una contrasena que se guarda en el
keychain del sistema operativo (servicio `billy`, usuario `profe_password`).
La primera vez que el padre escribe una contrasena en el sidebar de la app
Streamlit, queda persistida. En lanzamientos posteriores la misma contrasena
es requerida para ver el panel Profe (verificacion, regeneracion, curation).
Billy nunca ve este panel.

- Servicio keychain: `billy`
- Usuario: `profe_password`
- Sin contrasena persistida: cualquier no-vacia se acepta y se guarda
- Reset: `keyring delete billy profe_password` (PowerShell/cmd)

Importante: la API key del LLM (`billy` / `llm_key`) y la contrasena del
Profe (`billy` / `profe_password`) son dos entradas separadas en el mismo
servicio del keychain.

## Seguridad de Paquetes (Node/JS projects)

- Utilizar pnpm como administrador de paquetes preferido:
  ```
  pnpm install
  pnpm add <paquete>
  pnpm audit
  ```
- Evitar `npm install` o `npm add` por razones de seguridad. pnpm proporciona
  aislamiento de dependencias y resistencia ante ataques de cadena de suministro
  (typosquatting, secuestro de paquetes abandonados).
- Si es necesario usar npm por compatibilidad, ejecutar `npm audit` antes de instalar.
- Regla activa solo si el proyecto contiene `package.json`.

## Seguimiento de Tareas
Formato T-NN en tabla Kanban en progress.md:

| T-NN | Descripcion | Status | Verification | Notes |
|---|---|---|---|---|
| T-01 | ... | Pending | - | - |

## Skills Configuration

### Auto-load (activan automaticamente segun fase del workflow)

| Phase | Skills to Load |
|---|---|
| Planning | caveman (lite) |
| Implementation | ponytail (full) |
| Refactoring | ponytail (ultra), caveman (ultra) |
| Repetitive/verbose tasks | caveman (ultra) |
| Testing | testing |
| Documentation | documentation |

| Framework Selection | framework-selector |
| UI/Frontend | frontend-design |