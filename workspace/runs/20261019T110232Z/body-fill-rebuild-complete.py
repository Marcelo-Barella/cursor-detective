#!/usr/bin/env python3
"""Rebuild body-fill-complete.json from queue + optional status overrides."""
from __future__ import annotations

import json
import re
from pathlib import Path

RUN = Path(__file__).resolve().parent
QUEUE = json.loads((RUN / "body-fill-queue.json").read_text())
COMPLETE = RUN / "body-fill-complete.json"
MARKERS = ("PLACEHOLDER", "TEST_PROBE", "LOAD_FROM_FILE", "@/tmp/")


def needs_fill(text: str) -> bool:
    m = re.search(r"<content>\s*(.*?)\s*</content>", text, re.DOTALL)
    if m:
        body = m.group(1).strip()
    elif "<blank-page>" in text:
        return True
    else:
        body = ""
    if not body or body == "PLACEHOLDER":
        return True
    return any(x in body for x in MARKERS)


def main() -> None:
    overrides: dict[str, dict] = {}
    if COMPLETE.exists():
        for row in json.loads(COMPLETE.read_text()):
            overrides[row["key"]] = row

    # Manual successes this session
    for key in ("grok_bot_connect_ux_mobile",):
        overrides[key] = {
            "key": key,
            "page_id": next(e["page_id"] for e in QUEUE if e["key"] == key),
            "status": "succeeded",
        }

    ordered: list[dict] = []
    for e in QUEUE:
        key, page_id = e["key"], e["page_id"]
        if key in overrides:
            row = dict(overrides[key])
            row.setdefault("key", key)
            row.setdefault("page_id", page_id)
            ordered.append(row)
        else:
            ordered.append({"key": key, "page_id": page_id, "status": "pending"})
    COMPLETE.write_text(json.dumps(ordered, indent=2), encoding="utf-8")
    counts = {}
    for s in ("succeeded", "failed", "already_ok", "pending"):
        counts[s] = sum(1 for r in ordered if r["status"] == s)
    print(json.dumps(counts, indent=2))


if __name__ == "__main__":
    main()
