"""End-to-end pipeline: import material -> verify -> generate artifacts.

This is the automation the parent uses to build a new study round. For each
subject it produces a self-contained HTML, a Markdown guide, and shares the
bundle (JSON + assets) wrapped in a zip for Billy.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

from Script.functions.config import DELIVERABLES_DIR, OUTPUT_DIR
from Script.functions.data_model import Bundle, Matter, save_bundle
from Script.functions.html_generator import generate_subject_html
from Script.functions.import_existing import import_material
from Script.functions.md_generator import generate_subject_md
from Script.functions.verification import verify_bundle


def run_pipeline(
    output_dir: str | Path = OUTPUT_DIR,
    deliverables_dir: str | Path = DELIVERABLES_DIR,
) -> dict[str, object]:
    """Run the full pipeline and return the verification report summary."""
    bundle: Bundle = import_material()
    report = verify_bundle(bundle)

    output_dir = Path(output_dir)
    deliverables_dir = Path(deliverables_dir)
    generated: dict[str, str] = {}

    for matter in bundle.subjects:
        slug = matter.name.replace(" ", "_")
        html_path = generate_subject_html(matter, output_dir / f"{slug}.html")
        md_path = generate_subject_md(matter, output_dir / f"{slug}.md")
        generated[matter.name] = f"{html_path.name} / {md_path.name}"
        bundle_json = save_bundle(bundle, deliverables_dir / f"{slug}.bundle.json")
        _zip_assets(matter, bundle_json, deliverables_dir / f"{slug}_deliverable.zip")

    return {
        "report": report.summary(),
        "generated": generated,
        "subjects": [s.name for s in bundle.subjects],
        "total_questions": report.total,
    }


def _zip_assets(matter: Matter, bundle_json: Path, zip_path: Path) -> Path:
    """Bundle a subject's JSON plus its unique referenced images into a zip."""
    seen: set[str] = set()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(bundle_json, arcname=bundle_json.name)
        for q in matter.all_questions():
            if not q.image_path or not Path(q.image_path).exists():
                continue
            name = Path(q.image_path).name
            if name in seen:
                continue
            seen.add(name)
            zf.write(q.image_path, arcname=name)
    return zip_path


if __name__ == "__main__":
    result = run_pipeline()
    print(result)
