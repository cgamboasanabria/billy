# Billy - Diseno (design.md)

## Marco y decisiones

| Decision | Eleccion | Justificacion |
|---|---|---|
| Framework de trabajo | **Streamlit** | Dashboard Python, minimo overhead, acorde a AGENTS.md |
| Formato de entrega | **HTML estatico autocontenido** | Offline, multiplataforma (Windows/Linux Mint), sin instalar nada |
| Tutor IA | **OpenCode Zen** (OpenAI-compatible) | Api key barata y revocable; modelo `deepseek-v4-flash` (texto) y `minimax-m3` (vision) |
| Anclaje del tutor | Hibrido: **RAG** por defecto + **vision** para paginas impresas | Respuestas solo a partir de las fuentes oficiales |
| Almacen de la API key | **keyring** (almacen del SO) con fallback a entorno | La key queda bajo la cuenta del padre; el nino no la lee de un archivo |
| Unidad de actualizacion | **Bundle** (JSON + imagenes) | Compartir una carpeta/zip al actualizar contenido sin re-configurar |
| Persistencia | JSON (portable) | Sin base de datos, facil de transportar y versionar |

## Arquitectura

```
src/app.py                    Streamlit (vista estudiante)
Script/functions/
  config.py                   Rutas + config LLM
  data_model.py               Bundle/Matter/Module/Question + JSON
  import_existing.py          Importa guias MD, mapeo y quiz (3 formatos HTML)
  verification.py             Coherencia pregunta <-> cita <-> imagen
  html_generator.py           HTML autocontenido con imagenes base64
  md_generator.py             Guia estatica de repaso
  llm_client.py               Cliente OpenAI-compatible para OpenCode Zen + keyring
  rag.py                      RAG anclado + respuesta proactiva (temp ~0)
  vision.py                   Vision sobre pagina impresa (MiniMax M3)
  extract.py                  Texto de PDFs (pypdf) + OCR opcional
  pipeline.py                 Import -> verificacion -> generacion -> bundle
assets/originales/            Material fuente (imagenes, PDFs)
assets/mapeos/                Guias + mapeo + quiz HTML de referencia
Output/Results/               HTML + MD generados
Deliverables/                 Bundles (JSON + zip) para Billy
tests/                        pytest
```

## Flujo del pipeline

1. `import_material()` lee los quiz HTML (`allQuestions`, `questions`,
   `rawQuestions`) y el `mapeo_ciencias_definitivo.txt`, y construye un `Bundle`.
2. `verify_bundle()` marca errores (respuesta fuera de opciones, imagen sin
   resolver) y warnings (sin cita/tema/imagen).
3. `generate_subject_html()` produce HTML autocontenido: imagenes en base64
   (mapa deduplicado), barra de progreso, quiz con refuerzo del mismo tema al
   fallar, y explicacion con imagen + cita + boton Avanzar.
4. `pipeline.py` empaqueta el bundle en `Deliverables` (zip de JSON + imagenes).

## Procedimiento por tipo de fuente

Cada materia nueva de una ronda de examen se incorpora segun su fuente:

| Fuente | Formato | Proceso |
|---|---|---|
| Quiz HTML generado previamente | `allQuestions` / `questions` / `rawQuestions` | `import_existing._load_quiz_html` arma `Question` con opciones, cita, imagen y tema. Se importa solo en el pipeline. |
| Mapeo de imagenes (texto) | `mapeo_ciencias_definitivo.txt` | `import_existing._load_mapeo_txt` arma preguntas sin opciones (se curan despues). |
| Imagenes o PDFs de libros | Foto de pagina / PDF escaneado | Vision `minimax-m3` (`vision.py`) propone pregunta+opciones+cita; el padre aprueba y se guarda en `nuevas/*.json`; `_merge_curation` las integra. |
| PDFs con texto | PDF con capa de texto | `extract.py` usa `pypdf` (texto) y `ocr_image` para OCR opcional (requiere Tesseract). |

## Tratamiento de riesgos

- **Imagenes con rutas relativas (bug original):** resuelto con base64.
- **Mapeo imagen <-> pagina incompleto:** el verificador marca preguntas cuya
  imagen no existe; se provee o se excluye.
- **Preguntas abiertas sin opciones:** se excluyen del quiz interactivo (siguen
  en el material de estudio y la guia MD).
- **Hallucination del LLM:** RAG + abstinencia ("Eso no esta en tus apuntes")
  y temperatura 0; la key se guarda en el almacen del SO.
- **Pregunta fuera de los apuntes:** el tutor no se limita a abstenerse; lanza
  una pregunta reformulada de la ronda seleccionada (`rag.proactive_question`)
  para mantener el repaso en tema.
