import argparse
import json
import sys
from pathlib import Path

import numpy as np
import faiss
import torch
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM


def load_meta(meta_file: Path):
    rows = []
    with meta_file.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if len(line) == 0:
                continue
            rows.append(json.loads(line))
    return rows


def clean_text(s: str):
    t = s.strip()
    t = t.replace("SOURCES:", "").strip()
    t = t.replace("SOURCE", "").strip()
    t = t.replace("ID:", "").strip()
    t = t.replace("TEXT:", "").strip()
    if t.startswith("ANSWER:"):
        t = t[len("ANSWER:"):].strip()
    return t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--index_file", default="data/index/faiss.index")
    ap.add_argument("--meta_file", default="data/index/meta.jsonl")
    ap.add_argument("--embed_model", default="sentence-transformers/all-MiniLM-L6-v2")
    ap.add_argument("--gen_model", default="google/flan-t5-base")
    ap.add_argument("--query", required=True)
    ap.add_argument("--top_k", type=int, default=10)
    ap.add_argument("--cite_k", type=int, default=2)
    ap.add_argument("--min_score", type=float, default=0.35)
    ap.add_argument("--max_context_chars", type=int, default=9000)
    ap.add_argument("--max_new_tokens", type=int, default=140)
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

    embedder = SentenceTransformer(args.embed_model)

    qvec = embedder.encode([args.query], convert_to_numpy=True, normalize_embeddings=True)
    if qvec.dtype != np.float32:
        qvec = qvec.astype(np.float32)

    D, I = index.search(qvec, args.top_k)

    top_score = float(D[0][0])
    if top_score < args.min_score:
        print("FINAL: ABSTAIN (evidence score too low)")
        print(f"top_score={top_score:.4f} (min_score={args.min_score})")
        return

    retrieved = []
    for j in range(args.top_k):
        idx = int(I[0][j])
        score = float(D[0][j])
        r = rows[idx]
        doc_id = r.get("doc_id")
        chunk_id = r.get("chunk_id")
        page = r.get("page")
        text = r.get("text", "")
        retrieved.append((score, doc_id, chunk_id, page, text))

    print("=== RETRIEVED CHUNKS (evidence) ===")
    for j in range(len(retrieved)):
        score, doc_id, chunk_id, page, text = retrieved[j]
        preview = text[:220].replace("\n", " ")
        print(f"{j+1}. score={score:.4f} [{doc_id}:{chunk_id}] page={page}  {preview}")

    context_blocks = []
    used_chars = 0
    for score, doc_id, chunk_id, page, text in retrieved:
        block = f"ID: {doc_id}:{chunk_id}\nTEXT: {text}"
        if used_chars + len(block) > args.max_context_chars:
            break
        context_blocks.append(block)
        used_chars += len(block)

    context = "\n\n".join(context_blocks)

    tokenizer = AutoTokenizer.from_pretrained(args.gen_model)
    model = AutoModelForSeq2SeqLM.from_pretrained(args.gen_model)
    model.eval()

    prompt = (
        "Answer the QUESTION using ONLY the SOURCE TEXT below.\n"
        "Write 1-2 sentences. Do NOT copy long passages.\n"
        "If the sources do not support an answer, output exactly: ABSTAIN\n\n"
        f"QUESTION: {args.query}\n\n"
        f"SOURCE TEXT:\n{context}\n\n"
        "ANSWER:"
    )

    inputs = tokenizer(prompt, return_tensors="pt", truncation=True)
    with torch.no_grad():
        out = model.generate(
            **inputs,
            max_new_tokens=args.max_new_tokens,
            do_sample=False,
            num_beams=1,
            no_repeat_ngram_size=3,
        )

    ans = tokenizer.decode(out[0], skip_special_tokens=True).strip()
    ans = clean_text(ans)

    print("\n=== DRAFT ANSWER ===")
    print(ans)

    if ans == "ABSTAIN" or ans == "":
        print("\nFINAL: ABSTAIN")
        return

    k = args.cite_k
    if k < 1:
        k = 1
    if k > len(retrieved):
        k = len(retrieved)

    cites = []
    for j in range(k):
        _, doc_id, chunk_id, _, _ = retrieved[j]
        cites.append(f"[{doc_id}:{chunk_id}]")

    final_out = ans + " " + " ".join(cites)

    print("\n=== FINAL ANSWER (citations attached) ===")
    print(final_out)


if __name__ == "__main__":
    main()
