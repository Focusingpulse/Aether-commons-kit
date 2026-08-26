#!/usr/bin/env python3
"""chunk_book.py — split a long text file into translatable chunks.

Pure stdlib. Splits on paragraph boundaries near the target size so chunks
are readable units, writes chunks/chunk_NNN.txt plus chunks/manifest.json
with section headings and a per-chunk status field for the translator.

Usage:
    python3 chunk_book.py --input book_full_text.txt --out chunks/ [--size 1800]
    python3 chunk_book.py --input book_full_text.txt --out chunks/ --manifest existing/manifest.json  # resume
"""
import argparse, json, os, re, sys


def split_into_chunks(text, target):
    # Normalize newlines, keep paragraph breaks
    paras = re.split(r"\n\s*\n", text)
    chunks, cur = [], ""
    for para in paras:
        p = para.strip()
        if not p:
            continue
        if len(cur) + len(p) + 2 <= target:
            cur = cur + "\n\n" + p if cur else p
        else:
            if cur:
                chunks.append(cur)
            if len(p) > target:
                # paragraph alone exceeds target: hard-split on sentences
                parts = re.split(r"(?<=[.!?])\s+", p)
                buf = ""
                for part in parts:
                    if len(buf) + len(part) + 1 <= target:
                        buf = buf + " " + part if buf else part
                    else:
                        if buf:
                            chunks.append(buf)
                        buf = part
                if buf:
                    cur = buf
                else:
                    cur = ""
            else:
                cur = p
    if cur:
        chunks.append(cur)
    return chunks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--size", type=int, default=1800)
    ap.add_argument("--manifest", default=None, help="existing manifest to resume from")
    a = ap.parse_args()

    with open(a.input, encoding="utf-8", errors="replace") as f:
        text = f.read()
    chunks = split_into_chunks(text, a.size)

    os.makedirs(a.out, exist_ok=True)

    manifest_path = a.manifest or os.path.join(a.out, "manifest.json")
    if os.path.exists(manifest_path):
        with open(manifest_path, encoding="utf-8") as f:
            manifest = json.load(f)
        existing = {c["file"] for c in manifest.get("chunks", [])}
    else:
        manifest = {"book": os.path.basename(a.input), "total_chunks": len(chunks), "chunks": []}
        existing = set()

    added = 0
    for i, ch in enumerate(chunks, start=1):
        fname = f"chunk_{i:03d}.txt"
        if fname in existing:
            continue
        with open(os.path.join(a.out, fname), "w", encoding="utf-8") as f:
            f.write(ch)
        manifest["chunks"].append({"number": i, "file": fname, "chars": len(ch), "status": "pending"})
        added += 1
    manifest["total_chunks"] = len(chunks)

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    done = sum(1 for c in manifest["chunks"] if c.get("status") == "done")
    print(f"{added} new chunks written to {a.out} ({len(chunks)} total, {done} translated)")
    print(f"manifest: {manifest_path}")


if __name__ == "__main__":
    main()