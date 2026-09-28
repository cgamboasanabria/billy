# Mapa del proyecto Billy

Generado por `bstrd map` (deterministico: sin fechas ni rutas absolutas).

## Identidad
- Nombre: Billy
- Perfiles: web-app
- Entry points: ninguno

## Leer primero
- README.md
- AGENTS.md
- pyproject.toml
- openspec/proposal.md
- docs/PROJECT_MAP.md
- memory.md
- progress.md

## Estructura (nivel 1)
- AGENTS.md
- ActualizarBilly.bat
- Billy.code-workspace
- Deliverables/ (8 archivos)
- InstalarBilly.bat
- LanzarBilly.bat
- Output/ (8 archivos)
- README.md
- Script/ (16 archivos)
- assets/ (132 archivos)
- crear_acceso_directo.ps1
- docs/ (1 archivos)
- memory.md
- openspec/ (2 archivos)
- progress.md
- pyproject.toml
- requirements.txt
- src/ (1 archivos)
- uv.lock

## Modulos Python (17)
### Script/__init__.py
- Doc: Billy pipeline scripts (business logic lives under Script/functions).
### Script/diagnostico_llm.py
- Doc: Diagnostico del tutor LLM con una llamada real.
- def main()
### Script/functions/__init__.py
- Doc: Billy business-logic functions (pure, UI-agnostic).
### Script/functions/config.py
- Doc: Central configuration for the Billy project.
### Script/functions/curation.py
- Doc: Curation workflow: vision-proposed questions pending parent approval.
- def load_pending_proposals(subject)
- def save_proposal(subject, image_name, proposal)
- def approve_proposal(subject, image_name)
### Script/functions/data_model.py
- Doc: Data model for Billy study content.
- class Question
- class Module
- class Matter
- class Bundle
- def save_bundle(bundle, path)
- def load_bundle(path)
### Script/functions/extract.py
- Doc: Text extraction from source PDFs (and optional OCR).
- def extract_pdf_text(pdf_path)
- def ocr_image(image_path)
### Script/functions/html_generator.py
- Doc: Generate a self-contained interactive study HTML.
- def render_subject_html(matter)
- def generate_subject_html(matter, output_path)
- def json_dumps(value)
### Script/functions/import_existing.py
- Doc: Import existing study material into the data model.
- def import_material(quiz_html_dir, mapeo_txt, include_curation)
- def iter_questions(bundle)
### Script/functions/llm_client.py
- Doc: LLM client for the study tutor, using the OpenCode Zen endpoint.
- def store_api_key(key)
- def get_api_key()
- def get_llm_client()
- def tutor_answer(system, user, temperature, max_tokens, history)
- def describe_llm_error(exc)
### Script/functions/md_generator.py
- Doc: Generate a static Markdown study guide from a subject's questions.
- def generate_subject_md(matter, output_path)
### Script/functions/pipeline.py
- Doc: End-to-end pipeline: import material -> verify -> generate artifacts.
- def run_pipeline(output_dir, deliverables_dir)
### Script/functions/rag.py
- Doc: Retrieval-augmented generation for the grounded tutor.
- class Chunk
- def build_corpus(bundle)
- def retrieve(query, corpus, top_k)
- def build_topic_overview(bundle)
- def grounded_answer(query, bundle, top_k, asked, history)
- def proactive_question(bundle, asked)
### Script/functions/verification.py
- Doc: Cross-check the coherence of each Question.
- class Issue
- class VerificationReport
- def verify_bundle(bundle)
- def filter_ready(questions)
### Script/functions/vision.py
- (no parseable)
### Script/guardar_key.py
- Doc: Guarda la API key del tutor en el almacen del SO (keyring).
- def main()
### src/app.py
- Doc: Billy Web App - Streamlit dashboard (estudiante).
- def main()

## Agentes (.opencode/agents)
- business-finance: Acts as a Business Strategist and CFO (Chief Financial Officer) for projects, providing financial analysis, cost management, revenue model design, pricing strategy, and unit economics validation. Triggers when the user mentions business model, revenue architecture, monetization strategy, cost structure, pricing, break-even, ROI, NPV, IRR, unit economics, value proposition monetization, quality costs, contingency reserves, financial viability, stage gate reviews, budget estimation, WBS costing, scope protection, or any pre-design financial planning. Use this skill whenever the user wants to define their business model, estimate project budgets, validate financial viability, structure revenue models, or fill the "Diseno de Negocio y Finanzas" section in proposal.md files.
- buyer-persona: Acts as a market psychologist and digital anthropologist for building ultra-detailed buyer persona profiles. Triggers when the user mentions buyer persona, target audience, customer profile, user segmentation, early adopter, ideal client, customer pain points, desired gains, purchase triggers, cool hunting, marketing psychology, decision-making biases, must-have requirements, or any pre-design customer research. Use this skill whenever the user wants to define their ideal customer profile, understand target audience motivations and frustrations, build user personas for UX/UI design, identify purchase drivers, or segment users by demographics and behavioral patterns. Also triggers when working with proposal.md files or need to fill the "Perfil de Buyer Persona" section.
- planner: Guides the agent through a structured project planning workflow for software development and data science projects. Orchestrates iterative information gathering, scope definition, WBS creation, critical path analysis, and AI-assisted planning. Triggers when the user mentions project plan, project charter, scope statement, WBS, critical path, milestone planning, roadmap, CPM, resource allocation, change control, stage gate, closure criteria, time-to-market, or any pre-design project scheduling. Use this skill whenever the user wants to structure a project plan, create a work breakdown structure, define project scope, estimate timelines, validate feasibility, or fill the "Planificacion del Proyecto y Roadmap" section in proposal.md files.
- validator: Acts as a business analyst and hypothesis validator for startup ideas or client requirements. Triggers when the user mentions validating an idea, checking hypothesis viability, MVP planning, business feasibility, risk assessment, proposal.md, scope validation, assumption analysis, smoke tests, experiment design, kill points, buyer persona prep, or any pre-development business validation work. Use this skill whenever the user wants to validate their business idea before building, check if a project is viable, structure an MVP experiment, or analyze risks and assumptions of a proposed product. Also triggers when working with proposal.md files or need to fill the "Validacion de Hipotesis" section.

## Skills (.opencode/skills)
- agent-automation
- cognitive-doc-design
- dev-communication-protocol
- framework-selector
- mvp-streamlit
- operating-contract
- react-nextjs
- safety-hooks
- testing
- typescript
- user-content-gate

## Specs (openspec)
- specs: ninguna
- changes: ninguno

## Pipeline (dvc.yaml)
- (sin dvc.yaml)

## Tests
- Archivos: 11
- Funciones: 60

## Procedencia y verificacion
- `.opencode/*` es gestionado por `bstrd refresh`; drift: `bstrd refresh --dry-run`.
- Evidencia por tarea: `bstrd receipt create --task T-NN`.
