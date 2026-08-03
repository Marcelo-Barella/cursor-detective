#!/usr/bin/env python3
"""Read-only decode helper for Cursor composer conversationState blobs (agentKv)."""

from __future__ import annotations

import argparse
import base64
import json
import re
import sqlite3
import sys
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

BLOB_PREFIX = "agentKv:blob:"
HEX_HASH_RE = re.compile(r"^[0-9a-fA-F]{64}$")


def emit_header(script: str, note: str = "") -> None:
    print(f"script={script}")
    print("note=read-only")
    if note:
        print(f"detail={note}")


def kv(key: str, value: Any) -> None:
    print(f"{key}={value}")


def default_state_db() -> Path:
    home = Path.home()
    return home / ".config" / "Cursor" / "User" / "globalStorage" / "state.vscdb"


def open_db(path: Path) -> sqlite3.Connection:
    uri = f"file:{path}?mode=ro"
    return sqlite3.connect(uri, uri=True)


def normalize_blob_hash(raw: str) -> str:
    s = raw.strip()
    if s.startswith(BLOB_PREFIX):
        s = s[len(BLOB_PREFIX) :]
    if s.startswith("blob:"):
        s = s[5:]
    return s.lower()


def read_varint(data: bytes, pos: int) -> tuple[int, int]:
    result = 0
    shift = 0
    while pos < len(data):
        b = data[pos]
        pos += 1
        result |= (b & 0x7F) << shift
        if (b & 0x80) == 0:
            return result, pos
        shift += 7
        if shift > 63:
            raise ValueError("varint too long")
    raise ValueError("truncated varint")


@dataclass
class ProtoField:
    field: int
    wire: int
    wire_name: str
    value: Any


WIRE_NAMES = {0: "varint", 1: "fixed64", 2: "len", 5: "fixed32"}


def decode_protobuf(
    data: bytes,
    *,
    depth: int = 0,
    max_depth: int = 4,
    max_fields: int = 80,
) -> list[ProtoField]:
    fields: list[ProtoField] = []
    pos = 0
    while pos < len(data) and len(fields) < max_fields:
        try:
            tag, pos = read_varint(data, pos)
        except ValueError:
            break
        field_num = tag >> 3
        wire = tag & 0x07
        wire_name = WIRE_NAMES.get(wire, f"wire{wire}")
        if wire == 0:
            try:
                val, pos = read_varint(data, pos)
            except ValueError:
                break
            fields.append(ProtoField(field_num, wire, wire_name, val))
        elif wire == 1:
            if pos + 8 > len(data):
                break
            fields.append(ProtoField(field_num, wire, wire_name, data[pos : pos + 8].hex()))
            pos += 8
        elif wire == 2:
            try:
                length, pos = read_varint(data, pos)
            except ValueError:
                break
            if pos + length > len(data):
                break
            chunk = data[pos : pos + length]
            pos += length
            nested: list[ProtoField] | None = None
            if depth < max_depth and chunk and chunk[0] in (0x08, 0x0A, 0x10, 0x12, 0x1A, 0x22, 0x2A):
                try:
                    nested = decode_protobuf(
                        chunk, depth=depth + 1, max_depth=max_depth, max_fields=40
                    )
                except Exception:
                    nested = None
            text: str | None = None
            try:
                text = chunk.decode("utf-8")
                if not text.isprintable() and not any(c in text for c in "\n\r\t"):
                    text = None
            except UnicodeDecodeError:
                text = None
            fields.append(
                ProtoField(
                    field_num,
                    wire,
                    wire_name,
                    {
                        "len": length,
                        "utf8": text[:500] if text is not None else None,
                        "nested": nested,
                        "hex_head": chunk[:24].hex() if nested is None else None,
                    },
                )
            )
        elif wire == 5:
            if pos + 4 > len(data):
                break
            fields.append(ProtoField(field_num, wire, wire_name, data[pos : pos + 4].hex()))
            pos += 4
        else:
            break
    return fields


def extract_strings(data: bytes, min_len: int = 4) -> list[str]:
    out: list[str] = []
    cur: list[int] = []
    for b in data:
        if 32 <= b < 127 or b in (9, 10, 13):
            cur.append(b)
        else:
            if len(cur) >= min_len:
                out.append(bytes(cur).decode("ascii", errors="replace"))
            cur = []
    if len(cur) >= min_len:
        out.append(bytes(cur).decode("ascii", errors="replace"))
    return out


def fetch_blob(conn: sqlite3.Connection, blob_hash: str) -> bytes | None:
    key = BLOB_PREFIX + blob_hash
    row = conn.execute("SELECT value FROM cursorDiskKV WHERE key = ?", (key,)).fetchone()
    if not row or row[0] is None:
        return None
    val = row[0]
    if isinstance(val, memoryview):
        return bytes(val)
    if isinstance(val, bytes):
        return val
    return val.encode("latin-1", errors="surrogateescape")


def fetch_composer_json(conn: sqlite3.Connection, composer_id: str) -> dict[str, Any] | None:
    key = f"composerData:{composer_id}"
    row = conn.execute("SELECT value FROM cursorDiskKV WHERE key = ?", (key,)).fetchone()
    if not row or not row[0]:
        return None
    raw = row[0]
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    return json.loads(raw)


def classify_conversation_state(value: Any) -> str:
    if value is None:
        return "absent"
    if isinstance(value, dict):
        return "inline_json"
    if not isinstance(value, str):
        return "other"
    if len(value) == 0:
        return "empty"
    if value == "~":
        return "placeholder"
    if value.startswith("~"):
        return "tilde_base64_protobuf"
    if value.startswith("{"):
        return "inline_json_string"
    return "opaque_string"


def decode_tilde_envelope(cs: str) -> bytes | None:
    if not cs.startswith("~") or len(cs) < 2:
        return None
    try:
        return base64.b64decode(cs[1:] + "==", validate=False)
    except Exception:
        return None


def extract_blob_refs(data: bytes) -> list[tuple[int, str]]:
    refs: list[tuple[int, str]] = []
    pos = 0
    while pos < len(data):
        try:
            tag, pos = read_varint(data, pos)
        except ValueError:
            break
        wire = tag & 7
        field = tag >> 3
        if wire == 0:
            try:
                _, pos = read_varint(data, pos)
            except ValueError:
                break
        elif wire == 1:
            pos += 8
        elif wire == 2:
            try:
                length, pos = read_varint(data, pos)
            except ValueError:
                break
            if pos + length > len(data):
                break
            chunk = data[pos : pos + length]
            pos += length
            if length == 32:
                refs.append((field, chunk.hex()))
        elif wire == 5:
            pos += 4
        else:
            break
    return refs


BLOB_REF_FIELD_ROLES = {
    1: "state_chain",
    8: "aux",
    13: "checkpoint",
}


def find_hex_hashes_in_json(obj: Any) -> list[str]:
    found: list[str] = []

    def walk(x: Any) -> None:
        if isinstance(x, dict):
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
        elif isinstance(x, str) and HEX_HASH_RE.match(x):
            found.append(x.lower())

    walk(obj)
    return sorted(set(found))


def try_decompress(data: bytes) -> tuple[str, bytes] | None:
    for wbits in (zlib.MAX_WBITS | 32, zlib.MAX_WBITS, -zlib.MAX_WBITS):
        try:
            out = zlib.decompress(data, wbits)
            return ("zlib", out)
        except zlib.error:
            continue
    return None


def print_blob_report(blob_hash: str, data: bytes, *, dump_hex: int) -> None:
    kv("blob_hash", blob_hash)
    kv("byte_length", len(data))
    kv("head_hex", data[:32].hex())

    decomp = try_decompress(data)
    if decomp:
        label, payload = decomp
        kv("decompression", label)
        kv("decompressed_length", len(payload))
        data = payload

    try:
        text = data.decode("utf-8")
        json.loads(text)
        kv("detected_format", "json_utf8")
        print("json=")
        print(json.dumps(json.loads(text), indent=2)[:20000])
        return
    except (UnicodeDecodeError, json.JSONDecodeError):
        pass

    fields = decode_protobuf(data)
    if fields:
        kv("detected_format", "protobuf_wire")
        print("protobuf_fields=")
        for f in fields:
            print(f"  field={f.field} wire={f.wire_name} value={f.value!r}")
    else:
        kv("detected_format", "binary_unknown")

    strings = extract_strings(data)
    if strings:
        kv("printable_string_count", len(strings))
        print("strings=")
        for s in strings[:40]:
            line = s.replace("\n", "\\n")
            if len(line) > 200:
                line = line[:200] + "..."
            print(f"  {line}")

    if dump_hex > 0:
        print("hex_dump=")
        limit = min(len(data), dump_hex)
        for off in range(0, limit, 16):
            chunk = data[off : off + 16]
            hexpart = " ".join(f"{b:02x}" for b in chunk)
            asc = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
            print(f"  {off:08x}  {hexpart:<47}  {asc}")


def print_composer_report(conn: sqlite3.Connection, composer_id: str) -> None:
    data = fetch_composer_json(conn, composer_id)
    if data is None:
        kv("composer_data", "not_found")
        return
    kv("composer_id", composer_id)
    kv("composer_data_key", f"composerData:{composer_id}")
    kv("composer_v", data.get("_v"))
    kv("isNAL", data.get("isNAL"))
    kv("isAgentic", data.get("isAgentic"))
    kv("unifiedMode", data.get("unifiedMode"))

    cs = data.get("conversationState")
    kind = classify_conversation_state(cs)
    kv("conversationState_kind", kind)
    if isinstance(cs, str):
        kv("conversationState_length", len(cs))
        kv("conversationState_prefix", repr(cs[:24]))
    bek = data.get("blobEncryptionKey")
    if isinstance(bek, str):
        kv("blobEncryptionKey_length", len(bek))
        kv("has_blobEncryptionKey", "true")
    else:
        kv("has_blobEncryptionKey", "false")

    if kind == "tilde_base64_protobuf" and isinstance(cs, str):
        inner = decode_tilde_envelope(cs)
        if inner is None:
            print("warning=conversationState ~ envelope failed base64 decode")
        else:
            kv("conversationState_decoded_bytes", len(inner))
            refs = extract_blob_refs(inner)
            kv("conversationState_blob_ref_count", len(refs))
            if refs:
                print("conversationState_blob_refs=")
                for field, blob_hash in refs:
                    role = BLOB_REF_FIELD_ROLES.get(field, f"field{field}")
                    row = conn.execute(
                        "SELECT length(value) FROM cursorDiskKV WHERE key = ?",
                        (BLOB_PREFIX + blob_hash,),
                    ).fetchone()
                    nbytes = row[0] if row else 0
                    print(f"  [{role}] field={field} hash={blob_hash} agentKv_bytes={nbytes}")

    if kind == "inline_json" and isinstance(cs, dict):
        print("conversationState_json=")
        print(json.dumps(cs, indent=2)[:20000])

    hashes = find_hex_hashes_in_json(data)
    if hashes:
        kv("embedded_blob_hash_count", len(hashes))
        print("embedded_blob_hashes=")
        for h in hashes[:20]:
            print(f"  {h}")

    n_bubbles = conn.execute(
        "SELECT COUNT(*) FROM cursorDiskKV WHERE key LIKE ?",
        (f"bubbleId:{composer_id}:%",),
    ).fetchone()[0]
    kv("bubble_key_count", n_bubbles)


def list_blobs(conn: sqlite3.Connection, limit: int) -> None:
    rows = conn.execute(
        """
        SELECT key, length(value) AS n
        FROM cursorDiskKV
        WHERE key LIKE 'agentKv:blob:%'
        ORDER BY n DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    kv("blob_list_count", len(rows))
    print("blobs=")
    for key, nbytes in rows:
        h = key[len(BLOB_PREFIX) :]
        print(f"  {h}  {nbytes}B")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Decode Cursor agentKv conversation blobs from state.vscdb (read-only)."
    )
    parser.add_argument("--db", type=Path, help="Path to state.vscdb (default: global)")
    parser.add_argument("--composer-id", help="Inspect composerData row and conversationState metadata")
    parser.add_argument("--blob", help="agentKv blob hash (64 hex chars) or full agentKv:blob:... key")
    parser.add_argument("--list-blobs", type=int, metavar="N", help="List N largest agentKv:blob keys")
    parser.add_argument("--hex-dump", type=int, default=128, metavar="BYTES", help="Hex dump limit (0=off)")
    parser.add_argument("--out", type=Path, help="Write raw blob bytes to file")
    args = parser.parse_args()

    if not args.composer_id and not args.blob and not args.list_blobs:
        parser.error("one of --composer-id, --blob, or --list-blobs is required")

    db_path = args.db or default_state_db()
    if not db_path.is_file():
        print(f"error: state.vscdb not found: {db_path}", file=sys.stderr)
        return 1

    emit_header("decode-conversation-state.py")
    kv("db", str(db_path))

    conn = open_db(db_path)
    try:
        if args.list_blobs:
            list_blobs(conn, args.list_blobs)

        if args.composer_id:
            print_composer_report(conn, args.composer_id)

        if args.blob:
            blob_hash = normalize_blob_hash(args.blob)
            if not HEX_HASH_RE.match(blob_hash):
                print(f"error: invalid blob hash: {args.blob}", file=sys.stderr)
                return 1
            data = fetch_blob(conn, blob_hash)
            if data is None:
                kv("blob_found", "false")
                print(f"error: no row for {BLOB_PREFIX}{blob_hash}", file=sys.stderr)
                return 1
            kv("blob_found", "true")
            if args.out:
                args.out.write_bytes(data)
                kv("wrote_out", str(args.out))
            print_blob_report(blob_hash, data, dump_hex=args.hex_dump)
    finally:
        conn.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
