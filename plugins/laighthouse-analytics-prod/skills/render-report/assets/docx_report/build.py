"""CLI entrypoint: JSON section list -> .docx file.

Invoked directly as a script (not via -m), so it adds its own directory to
sys.path to resolve the sibling `sections`/`charts` modules regardless of
the caller's working directory.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from docx import Document  # noqa: E402

import sections as sec  # noqa: E402

_RENDERERS = {
    "heading": lambda doc, s: sec.add_heading(doc, s["text"]),
    "kpi_cards": lambda doc, s: sec.add_kpi_cards(doc, s["cards"]),
    "table": lambda doc, s: sec.add_data_table(doc, s.get("heading"), s["headers"], s["rows"]),
    "chart": lambda doc, s: sec.add_combo_chart_section(
        doc, s.get("heading"), s["categories"], s["bar_series"], s["line_series"]
    ),
    "text": lambda doc, s: sec.add_text_section(doc, s.get("heading"), s["body"]),
}


def build_document(data):
    document = Document()
    sec.add_title(document, data["title"], data.get("period"))
    for section in data["sections"]:
        stype = section["type"]
        renderer = _RENDERERS.get(stype)
        if renderer is None:
            raise ValueError(f"unknown section type: {stype}")
        renderer(document, section)
    return document


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True, help="path to the section-list JSON file")
    parser.add_argument("--out", required=True, help="path to write the .docx file to")
    args = parser.parse_args()

    data = json.loads(Path(args.data).read_text(encoding="utf-8"))
    document = build_document(data)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    document.save(out_path)


if __name__ == "__main__":
    main()
