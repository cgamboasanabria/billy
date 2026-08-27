---
# Project specifications: Billy

## 1. Hypotesis validation
La herramienta debe automatizar la generacion de material de estudio para Billy
(nina/o de cuarto grado en Costa Rica) a partir de fotos de libros y PDFs, y
entregar material autocontenido (HTML offline) que se vea en Windows y Linux
Mint. El valor real es el tutor conversacional anclado a las fuentes oficiales.

## 2. Buyer Persona
Ver validacion y entrevista previas. Usuario primario: Billy (estudiante de
primaria). Usuario editor: el padre (Cesar), que revisa y comparte contenidos.

## 3. Business Design and Finance
Herramienta personal/sin costo de licencias. Unico costo: API key del LLM
(OpenCode Zen), dedicada y revocable ("Billy"), usada a temperatura ~0.

## 4. Planification and roadmap
MVP entregado (T-01..T-31). Estado actual: solo vista estudiante (modo Profe
eliminado), rondas de examen (`marzo 2026` / `septiembre 2026`), tutor
proactivo, vision con MiniMax M3. Pendientes diferidos hasta contar con los
insumos de septiembre de las demas materias: QA manual, curacion de preguntas
abiertas (Ciencias, ronda marzo), JS bridge quiz->tutor, compresion de imagenes
(Pillow), editor inline de vision, OCR Tesseract y curation E2E con imagenes.

## 5. UI Framework Selection
- **Framework elegido:** Streamlit (herramienta de trabajo) + HTML estatico autocontenido (entrega a Billy)
- **Justificacion:** Streamlit es lo mas simple para el dashboard/pipeline Python del AGENTS.md. La entrega debe ser offline y multiplataforma (Windows/Linux Mint); un HTML con imagenes en base64 cumple eso sin instalar nada, y se genero con el arreglo del bug de compatibilidad (antes las imagenes apuntaban a rutas relativas).
- **Comando de instalacion:** uv sync (ver pyproject.toml). Chat tutor via OpenCode Zen: `uv run streamlit run src/app.py`
