import argparse
import json
import sys
from pathlib import Path

import numpy as np
import faiss
from sentence_transformers import SentenceTransformer


def load_meta(meta_file: Path):
    rows = []
    with meta_file.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if len(line) == 0:
                continue
            rows.append(json.loads(line))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--index_file", default="data/index/faiss.index")
    ap.add_argument("--meta_file", default="data/index/meta.jsonl")
    ap.add_argument("--model", default="sentence-transformers/all-MiniLM-L6-v2")
    ap.add_argument("--query", required=True)
    ap.add_argument("--top_k", type=int, default=5)
    args = ap.parse_args()

    index_file = Path(args.index_file)
    meta_file = Path(args.meta_file)

    if not index_file.exists():
        print(f"ERROR: index_file not found: {index_file}", file=sys.stderr)
        sys.exit(1)
    if not meta_file.exists():
        print(f"ERROR: meta_file not found: {meta_file}", file=sys.stderr)
        sys.exit(1)

    rows = load_meta(meta_file)

    index = faiss.read_index(str(index_file))
    model = SentenceTransformer(args.model)

    qvec = model.encode([args.query], convert_to_numpy=True, normalize_embeddings=True)
    if qvec.dtype != np.float32:
        qvec = qvec.astype(np.float32)

    D, I = index.search(qvec, args.top_k)

    print(f"QUERY: {args.query}")
    for j in range(args.top_k):
        idx = int(I[0][j])
        score = float(D[0][j])
        r = rows[idx]
        doc_id = r.get("doc_id")
        chunk_id = r.get("chunk_id")
        page = r.get("page")
        text_preview = r.get("text", "")[:180].replace("\n", " ")
        print(f"{j+1}. score={score:.4f} [{doc_id}:{chunk_id}] page={page}  {text_preview}")


if __name__ == "__main__":
    main()
