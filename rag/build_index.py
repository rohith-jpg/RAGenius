import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np
import faiss
from sentence_transformers import SentenceTransformer


def load_chunks(chunks_file: Path):
    rows = []
    with chunks_file.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if len(line) == 0:
                continue
            obj = json.loads(line)
            rows.append(obj)
    return rows


def save_meta(meta_file: Path, rows):
    with meta_file.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chunks_file", default="data/chunks/chunks.jsonl")
    ap.add_argument("--out_dir", default="data/index")
    ap.add_argument("--model", default="sentence-transformers/all-MiniLM-L6-v2")
    ap.add_argument("--batch_size", type=int, default=64)
    ap.add_argument("--query", default="")
    ap.add_argument("--top_k", type=int, default=5)
    args = ap.parse_args()

    chunks_file = Path(args.chunks_file)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if not chunks_file.exists():
        print(f"ERROR: chunks_file not found: {chunks_file}", file=sys.stderr)
        sys.exit(1)

    rows = load_chunks(chunks_file)
    if len(rows) == 0:
        print("ERROR: no rows loaded from chunks_file", file=sys.stderr)
        sys.exit(1)

    texts = []
    for r in rows:
        texts.append(r["text"])

    print(f"rows_loaded={len(rows)}")
    print(f"embedding_model={args.model}")

    model = SentenceTransformer(args.model)

    emb = model.encode(
        texts,
        batch_size=args.batch_size,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    if emb.dtype != np.float32:
        emb = emb.astype(np.float32)

    dim = int(emb.shape[1])
    print(f"embedding_dim={dim}")

    index = faiss.IndexFlatIP(dim)
    index.add(emb)

    index_file = out_dir / "faiss.index"
    faiss.write_index(index, str(index_file))

    meta_file = out_dir / "meta.jsonl"
    save_meta(meta_file, rows)

    info = {
        "chunks_file": str(chunks_file),
        "rows": int(len(rows)),
        "dim": int(dim),
        "model": args.model,
        "metric": "cosine_via_normalized_inner_product",
    }
    info_file = out_dir / "info.json"
    info_file.write_text(json.dumps(info, indent=2), encoding="utf-8")

    print(f"index_saved={index_file}")
    print(f"meta_saved={meta_file}")
    print(f"info_saved={info_file}")

    if len(args.query) > 0:
        q = args.query
        qvec = model.encode([q], convert_to_numpy=True, normalize_embeddings=True)
        if qvec.dtype != np.float32:
            qvec = qvec.astype(np.float32)

        D, I = index.search(qvec, args.top_k)

        print("")
        print(f"QUERY: {q}")
        k = int(args.top_k)
        for j in range(k):
            idx = int(I[0][j])
            score = float(D[0][j])
            r = rows[idx]
            doc_id = r.get("doc_id")
            chunk_id = r.get("chunk_id")
            page = r.get("page")
            text_preview = r.get("text", "")[:160].replace("\n", " ")
            print(f"{j+1}. score={score:.4f} [{doc_id}:{chunk_id}] page={page}  {text_preview}")


if __name__ == "__main__":
    main()
