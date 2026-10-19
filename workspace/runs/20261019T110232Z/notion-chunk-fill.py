#!/usr/bin/env python3
"""Chunk a plan markdown into Notion update steps (replace + insert_content)."""
import json
import sys
from pathlib import Path

CHUNK = 6000


def steps_for_key(key: str) -> list[dict]:
    run = Path(__file__).resolve().parent
    q = json.loads((run / "body-fill-queue.json").read_text())
    e = next(x for x in q if x["key"] == key)
    text = Path(e["plan"]).read_text()
    page_id = e["page_id"]
    chunks = [text[i : i + CHUNK] for i in range(0, len(text), CHUNK)]
    out: list[dict] = []
    out.append(
        {
            "page_id": page_id,
            "command": "replace_content",
            "new_str": chunks[0],
            "allow_async": True,
        }
    )
    for c in chunks[1:]:
        out.append(
            {
                "page_id": page_id,
                "command": "insert_content",
                "content": c,
                "position": {"type": "end"},
                "allow_async": True,
            }
        )
    return out


if __name__ == "__main__":
    key = sys.argv[1]
    steps = steps_for_key(key)
    print(json.dumps({"key": key, "steps": steps, "n": len(steps)}))
