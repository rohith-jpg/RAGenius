import argparse
import json
import os
import re
import sys
from pathlib import Path

import fitz


def normalize_text(s: str) -> str:
    s = s.replace("\x00", " ")
    s = re.sub(r"\s+", " ", s)
    s = s.strip()
    return s


def chunk_text(text: str, chunk_chars: int, overlap_chars: int):
    chunks = []
    if chunk_chars <= 0:
        return chunks
    if overlap_chars < 0:
        overlap_chars = 0
    if overlap_chars >= chunk_chars:
        overlap_chars = chunk_chars - 1

    n = len(text)
    if n == 0:
        return chunks

    stride = chunk_chars - overlap_chars
    i = 0
    while i < n:
        j = i + chunk_chars
        if j > n:
            j = n
        part = text[i:j]
        part = part.strip()
        if len(part) > 0:
            chunks.append(part)
        if j >= n:
            break
        i = i + stride

    return chunks


def read_text_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        try:
            return path.read_text(errors="ignore")
        except Exception:
            return ""


def iter_inputs(in_dir: Path):
    exts = [".pdf", ".txt", ".md"]
    files = []
    for p in in_dir.rglob("*"):
        if p.is_file():
            suf = p.suffix.lower()
            if suf in exts:
                files.append(p)
    files.sort()
    return files


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in_dir", default="data/sample_docs")
    ap.add_argument("--out_file", default="data/chunks/chunks.jsonl")
    ap.add_argument("--chunk_chars", type=int, default=2000)
    ap.add_argument("--overlap_chars", type=int, default=300)
    args = ap.parse_args()

    in_dir = Path(args.in_dir)
    out_file = Path(args.out_file)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    if not in_dir.exists() or not in_dir.is_dir():
        print(f"ERROR: in_dir not found: {in_dir}", file=sys.stderr)
        sys.exit(1)

    files = iter_inputs(in_dir)
    if len(files) == 0:
        print(f"ERROR: no input files found under: {in_dir}", file=sys.stderr)
        sys.exit(1)

    docs_processed = 0
    total_chunks = 0

    with out_file.open("w", encoding="utf-8") as f_out:
        for path in files:
            doc_id = path.stem
            source_name = path.name
            chunk_counter = 1

            suf = path.suffix.lower()

            if suf == ".pdf":
                try:
                    pdf = fitz.open(str(path))
                except Exception as e:
                    print(f"WARN: failed to open PDF: {path} ({e})", file=sys.stderr)
                    continue

                docs_processed += 1

                page_index = 0
                while page_index < pdf.page_count:
                    try:
                        page = pdf.load_page(page_index)
                        text = page.get_text("text")
                    except Exception:
                        text = ""

                    text = normalize_text(text)
                    if len(text) > 0:
                        parts = chunk_text(text, args.chunk_chars, args.overlap_chars)
                        for part in parts:
                            chunk_id = "c" + str(chunk_counter).zfill(4)
                            row = {
                                "doc_id": doc_id,
                                "source_name": source_name,
                                "page": page_index + 1,
                                "chunk_id": chunk_id,
                                "text": part,
                            }
                            f_out.write(json.dumps(row, ensure_ascii=False) + "\n")
                            chunk_counter += 1
                            total_chunks += 1

                    page_index += 1

                try:
                    pdf.close()
                except Exception:
                    pass

            else:
                raw = read_text_file(path)
                raw = normalize_text(raw)
                docs_processed += 1

                if len(raw) > 0:
                    parts = chunk_text(raw, args.chunk_chars, args.overlap_chars)
                    for part in parts:
                        chunk_id = "c" + str(chunk_counter).zfill(4)
                        row = {
                            "doc_id": doc_id,
                            "source_name": source_name,
                            "page": None,
                            "chunk_id": chunk_id,
                            "text": part,
                        }
                        f_out.write(json.dumps(row, ensure_ascii=False) + "\n")
                        chunk_counter += 1
                        total_chunks += 1

    print(f"docs_processed={docs_processed}")
    print(f"chunks_written={total_chunks}")
    print(f"out_file={out_file}")


if __name__ == "__main__":
    main()
