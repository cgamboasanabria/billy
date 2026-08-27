# Billy — Web Application

## Qué es

Herramientas educativas para Billy (estudiante de cuarto grado de Costa Rica).
Un Streamlit app que genera material de estudio (HTML autocontenido + guía
Markdown) a partir de fotos de libros y PDFs, y un tutor IA que responde **solo
a partir de las fuentes oficiales** (temperatura ~0, RAG + visión). Cuando el
estudiante pregunta algo que no está en los apuntes, el tutor en vez de
abstenerse lanza una pregunta reformulada de la ronda seleccionada.

## Stack

- Python >= 3.11
- **Streamlit** (herramienta de trabajo)
- **HTML estático autocontenido** (entrega a Billy, imágenes base64, offline,
  multiplataforma Windows/Linux Mint)
- LLM: **OpenCode Zen** (OpenAI-compatible), modelo `deepseek-v4-flash`
  (texto) y `minimax-m3` (visión)
- Persistencia: JSON portable (bundle)
- API key: almacén seguro del SO (`keyring`), key dedicada y revocable

## Estructura

```
src/app.py                 App Streamlit (vista estudiante: materia + ronda + quiz + tutor)
Script/functions/          Lógica de negocio (data_model, import_existing,
                           html_generator, md_generator, verification,
                           llm_client, rag, vision, extract, pipeline)
assets/originales/         Material fuente (imágenes, PDFs)
assets/mapeos/             Guías, mapeo y quiz HTML de referencia
Output/Results/            HTML + MD generados
Deliverables/              Bundles (JSON + zip) para Billy
openspec/                  proposal.md, design.md
tests/                     pytest
```

## Puesta en marcha

**Una sola vez (instalar dependencias):**

```bash
uv sync
```

**Lanzar la app (forma fácil, doble clic):**

Haz doble clic en **`LanzarBilly.bat`** en la raíz del proyecto. Activa el
entorno, inicia Streamlit y abre la app en el navegador.

**Lanzar desde terminal:**

```bash
uv run streamlit run src/app.py
```

## Instalacion en la maquina de Billy

La app se distribuye por un repo GitHub publico: Billy clona una sola vez y
despues actualiza el contenido con un doble clic, sin necesitar cuenta de
GitHub ni token (clonado anonimo).

**Primera vez (en persona):**

1. En la maquina de Billy, instala git si no esta (una sola vez, en PowerShell):

   ```powershell
   winget install --id Git.Git -e --source winget --accept-package-agreements --accept-source-agreements
   ```

2. Abre una terminal en la carpeta donde quieras dejar el proyecto y clona el repo:

   ```bash
   git clone https://github.com/cgamboasanabria/billy.git
   cd billy
   ```

3. Haz doble clic en **`InstalarBilly.bat`**. Instala uv (si falta), prepara el
   entorno, te pide la API key (enmascarada) y crea un acceso directo "Billy"
   en el escritorio.
4. De ahora en adelante, Billy abre la app con el acceso directo del escritorio.

**Actualizar el contenido (cada ronda nueva):**

Billy hace doble clic en **`ActualizarBilly.bat`** (o crea un acceso directo a
este). Hace `git pull` + `uv sync` y relanza la app. La API key del keyring no
se toca.

## Flujo del padre (actualizar el contenido)

1. Desarrolla la materia nueva en tu maquina (pipeline + vision).
2. Confirma y sube los cambios:

   ```bash
   git add assets/mapeos assets/originales src Script
   git commit -m "Ronda septiembre 2026: <materia>"
   git push
   ```

3. Billy ejecuta `ActualizarBilly.bat` y recibe la actualizacion.

**Nota de seguridad:** el repo es publico, asi que no debe contener secretos.
La API key vive en el keyring del SO (nunca en un archivo versionado). Los PDFs
de libros (`assets/libros/`) estan fuera del repo por peso y copyright.

## Pipeline

```bash
uv run python -m Script.functions.pipeline   # import -> verificar -> generar
```

Genera por materia: HTML autocontenido (imagín bases64, progreso, refuerzo por
tema al fallar), guía `.md`, y bundle (`Deliverables/`).

### Flujo de contenido por tipo de fuente

El importer (`Script/functions/import_existing.py`) distingue tres formatos de
entrada. Cada materia nueva se procesa según su fuente:

| Fuente | Formato | Proceso | Donde se refleja |
|---|---|---|---|
| Quiz HTML generado previamente | `const allQuestions = [...]` (Ciencias), `questions` (Español) o `rawQuestions` (Estudios Sociales) | `import_existing._load_quiz_html` parsea la lista y arma `Question` con opciones, cita, imagen y tema | `assets/mapeos/quiz_html/*.html` |
| Mapeo de imágenes (texto) | `mapeo_ciencias_definitivo.txt` (Archivo/Pregunta/Respuesta/Cita) | `import_existing._load_mapeo_txt` arma preguntas **sin opciones** (se curan luego) | `assets/mapeos/*.txt` |
| Imágenes o PDFs de libros | Foto de página o PDF escaneado | Visión con `minimax-m3` (`vision.py`) propone pregunta+opciones+cita; se aprueba y guarda en `nuevas/*.json` para que `_merge_curation` las integre | `assets/mapeos/nuevas/*.json` |

**PDFs con texto:** `extract.py` usa `pypdf` para extraer texto y `ocr_image`
para OCR opcional (requiere binario Tesseract).

Para replicar el procedimiento en una materia nueva de la ronda de septiembre:
1. Coloca la fuente en `assets/originales/` o `assets/mapeos/`.
2. Si es quiz HTML, se importa solo en el pipeline.
3. Si son imágenes/PDF, usa el flujo de visión para proponer preguntas y
   aprobarlas en `assets/mapeos/nuevas/<materia>.json`.
4. Corre el pipeline y revisa el reporte de `verify_bundle`.

## Comandos de calidad

```bash
uv run pytest --cov-fail-under=80
uv run ruff check Script/ src/ tests/
uv run black --check Script/ src/ tests/
```

## Nota de seguridad

La API key del LLM se guarda en el almacén del sistema (keyring) mediante
`InstalarBilly.bat` o `Script/guardar_key.py`. Es una key dedicada y revocable;
si hay uso indebido, se desactiva. Nunca viaja dentro del HTML entregado a
Billy ni queda escrita en archivos del proyecto.
