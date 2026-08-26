#!/usr/bin/env python3
"""assemble_translation.py — stitch translated chunks into a full document.

Pure stdlib. Reads chunks/manifest.json, collects every chunk that has a
translated sibling (chunk_NNN.en.txt), marks the manifest, and writes the
assembled full translation (with section headings) to
<book>_full_translation.md. Safe to run any time — idempotent.

The translator (Scribe) runs this after each batch to update progress and
publish the assembled document.

Usage:
    python3 assemble_translation.py --chunks chunks/ --out .
"""
import argparse, json, os, re, sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chunks", required=True, help="folder with chunk_NNN.txt + manifest.json")
    ap.add_argument("--out", default=".", help="where to write <book>_full_translation.md")
    a = ap.parse_args()

    manifest_path = os.path.join(a.chunks, "manifest.json")
    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)

    book = manifest.get("book", "book")
    out_path = os.path.join(a.out, book.replace(".txt", "") + "_full_translation.md")

    parts, done = [], 0
    for c in manifest.get("chunks", []):
        base = os.path.join(a.chunks, c["file"])
        en = base.replace(".txt", ".en.txt")
        if os.path.exists(en):
            with open(en, encoding="utf-8") as f:
                body = f.read().strip()
            section = c.get("section") or c["file"]
            parts.append(f"\n\n## Chunk {c['number']} — {section}\n\n{body}\n")
            if c.get("status") != "done":
                c["status"] = "done"
            done += 1

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    total = len(manifest.get("chunks", []))
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"# {book} — English Translation\n\nProgress: {done}/{total} chunks\n")
        f.write("".join(parts))

    print(f"assembled: {out_path} ({done}/{total} chunks translated)")
    if done < total:
        print(f"next pending: {manifest['chunks'][done]['file']}" if done < total else "")
    else:
        print("COMPLETE — full translation assembled")


if __name__ == "__main__":
    main()