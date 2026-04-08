#!/usr/bin/env python3
import argparse
import json
import sys
from typing import Any, Dict, List


def normalize_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def json_to_markdown_table(data: List[Dict[str, Any]]) -> str:
    if not data:
        return ""

    headers = []
    seen = set()
    for row in data:
        if isinstance(row, dict):
            for key in row.keys():
                if key not in seen:
                    seen.add(key)
                    headers.append(key)

    if not headers:
        return ""

    lines = []
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

    for row in data:
        values = [normalize_value(row.get(header, "")) if isinstance(row, dict) else "" for header in headers]
        lines.append("| " + " | ".join(values) + " |")

    return "\n".join(lines)


def load_json(source: str | None) -> Any:
    if source:
        with open(source, "r", encoding="utf-8") as f:
            return json.load(f)
    return json.load(sys.stdin)


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert JSON data into a Markdown table")
    parser.add_argument("input", nargs="?", help="Path to JSON file. If omitted, reads from stdin.")
    args = parser.parse_args()

    data = load_json(args.input)

    if not isinstance(data, list):
        raise SystemExit("Input JSON must be an array of objects.")

    table = json_to_markdown_table(data)
    print(table)


if __name__ == "__main__":
    main()
