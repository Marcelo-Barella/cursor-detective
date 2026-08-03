#!/usr/bin/env python3
"""Extract client feature gates from workbench kFe registry."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


FLAG_RE = re.compile(
    r"([a-zA-Z0-9_]+):\{client:(!0|!1),default:(!0|!1)\}"
)


def find_workbench(extract_dir: Path) -> Path:
    matches = list(extract_dir.rglob("workbench.desktop.main.js"))
    if not matches:
        raise SystemExit(f"workbench.desktop.main.js not found under {extract_dir}")
    matches.sort(key=lambda p: len(str(p)))
    return matches[0]


def extract_kfe_blob(data: str) -> str:
    idx = data.find("kFe={")
    if idx < 0:
        raise SystemExit("kFe={ registry not found in workbench bundle")
    i = idx + len("kFe=")
    if data[i] != "{":
        raise SystemExit("kFe assignment is not an object literal")
    depth = 0
    for j in range(i, len(data)):
        c = data[j]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return data[i : j + 1]
    raise SystemExit("failed to brace-match kFe object")


def parse_flags(blob: str) -> list[dict]:
    flags = []
    for name, client, default in FLAG_RE.findall(blob):
        flags.append(
            {
                "name": name,
                "client": client == "!0",
                "default": default == "!0",
            }
        )
    if not flags:
        raise SystemExit("no kFe flag entries matched expected shape")
    return flags


def category_for(name: str) -> str:
    prefix = name.split("_", 1)[0]
    mapping = {
        "glass": "glass",
        "cloud": "cloud",
        "agent": "agent",
        "composer": "composer",
        "mcp": "mcp",
        "automations": "automations",
        "browser": "browser",
        "codebase": "codebase",
        "bugbot": "bugbot",
        "cli": "cli",
        "model": "models",
        "ai": "models",
        "show": "ui",
        "customize": "ui",
        "sand": "other",
    }
    return mapping.get(prefix, "other")


def load_names(path: Path | None) -> set[str]:
    if path is None or not path.is_file():
        return set()
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".json":
        payload = json.loads(text)
        if isinstance(payload, dict) and "flags" in payload:
            return {f["name"] for f in payload["flags"]}
        if isinstance(payload, list):
            return {str(x) for x in payload}
        raise SystemExit(f"unsupported previous catalog JSON shape: {path}")
    return {line.strip() for line in text.splitlines() if line.strip()}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--extract-dir", required=True)
    parser.add_argument("--version-env", required=True)
    parser.add_argument("--previous-names", default="")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    extract_dir = Path(args.extract_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    version = ""
    commit_sha = ""
    download_url = ""
    env_path = Path(args.version_env)
    if env_path.is_file():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("VERSION="):
                version = line.split("=", 1)[1].strip().strip("'\"")
            elif line.startswith("COMMIT_SHA="):
                commit_sha = line.split("=", 1)[1].strip().strip("'\"")
            elif line.startswith("DOWNLOAD_URL="):
                download_url = line.split("=", 1)[1].strip().strip("'\"")

    workbench = find_workbench(extract_dir)
    data = workbench.read_text(encoding="utf-8", errors="replace")
    blob = extract_kfe_blob(data)
    flags = parse_flags(blob)
    names = [f["name"] for f in flags]
    previous = load_names(Path(args.previous_names) if args.previous_names else None)
    current = set(names)
    new_flags = sorted(current - previous)
    removed_flags = sorted(previous - current)

    inventory = {
        "source": "kFe in workbench.desktop.main.js",
        "version": version,
        "commit_sha": commit_sha,
        "download_url": download_url,
        "workbench_js": str(workbench),
        "count": len(flags),
        "flags": flags,
    }
    manifest = {
        "version": version,
        "commit_sha": commit_sha,
        "download_url": download_url,
        "workbench_js": str(workbench),
        "flag_count": len(flags),
        "new_flags_count": len(new_flags),
        "removed_flags_count": len(removed_flags),
        "new_flags": [
            {
                "name": name,
                "client": next(f["client"] for f in flags if f["name"] == name),
                "default": next(f["default"] for f in flags if f["name"] == name),
                "category": category_for(name),
            }
            for name in new_flags
        ],
        "removed_flags": removed_flags,
        "inventory_path": str(output_dir / "feature-flags-inventory.json"),
        "names_path": str(output_dir / "feature-flags-names.txt"),
    }

    (output_dir / "feature-flags-inventory.json").write_text(
        json.dumps(inventory, indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "feature-flags-names.txt").write_text(
        "\n".join(names) + "\n", encoding="utf-8"
    )
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )

    print(f"workbench_js={workbench}")
    print(f"flag_count={len(flags)}")
    print(f"new_flags_count={len(new_flags)}")
    print(f"removed_flags_count={len(removed_flags)}")
    print(f"manifest={output_dir / 'manifest.json'}")


if __name__ == "__main__":
    main()
