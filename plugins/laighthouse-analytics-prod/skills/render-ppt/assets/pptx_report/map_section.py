"""CLI entrypoint: raw MCP response JSON -> {sections, digest} JSON.

Invoked directly as a script (not via -m), so it adds its own directory to
sys.path to resolve the sibling `section_mapping` module regardless of the
caller's working directory.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import section_mapping as sm  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report-type", required=True, help="e.g. mtd")
    parser.add_argument("--group", required=True, help="section group id, e.g. A")
    parser.add_argument("--data", required=True, help="path to the raw MCP response JSON file")
    parser.add_argument("--out", required=True, help="path to write the {sections, digest} JSON file to")
    args = parser.parse_args()

    data = json.loads(Path(args.data).read_text(encoding="utf-8"))
    result = sm.map_section(args.report_type, args.group, data)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
