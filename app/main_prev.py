import json
from pathlib import Path
from typing import List, Optional, Dict, Any

import numpy as np
import faiss
import torch
from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM


class AskRequest(BaseModel):
    query: str
    top_k: int = 10
    cite_k: int = 2
    min_score: float = 0.35
    max_context_chars: int = 9000
    max_new_tokens: int = 140
    include_evidence: bool = True


class ChunkOut(BaseModel):
    score: float
    doc_id: str
    chunk_id: str
    page: Optional[int]
    text_preview: str


class AskResponse(BaseModel):
    query: str
    abstained: bool
    answer: str
    citations: List[str]
    top_chunks: Optional[List[ChunkOut]] = None


APP_ROOT = Path(".")
INDEX_FILE = APP_ROOT / "data/index/faiss.index"
META_FILE = APP_ROOT / "data/index/meta.jsonl"

EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
GEN_MODEL = "google/flan-t5-base"

_rows = None
_index = None
_embedder = None
_tokenizer = None
_gen_model = None


def _load_meta(meta_file: Path):
    rows = []
    with meta_file.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if len(line) == 0:
                continue
            rows.append(json.loads(line))
    return rows


def _clean_answer(s: str):
    t = s.strip()
    if t.startswith("ANSWER:"):
        t = t[len("ANSWER:"):].strip()
    return t


def _retrieve(query: str, top_k: int):
    qvec = _embedder.encode([query], convert_to_numpy=True, normalize_embeddings=True)
    if qvec.dtype != np.float32:
        qvec = qvec.astype(np.float32)

    D, I = _index.search(qvec, top_k)

    retrieved = []
    for j in range(top_k):
        idx = int(I[0][j])
        score = float(D[0][j])
        r = _rows[idx]
        doc_id = r.get("doc_id", "")
        chunk_id = r.get("chunk_id", "")
        page = r.get("page", None)
        text = r.get("text", "")
        retrieved.append((score, doc_id, chunk_id, page, text))
    return retrieved


def _build_context(retrieved, max_context_chars: int):
    blocks = []
    used = 0
    for score, doc_id, chunk_id, page, text in retrieved:
        block = f"ID: {doc_id}:{chunk_id}\nTEXT: {text}"
        if used + len(block) > max_context_chars:
            break
        blocks.append(block)
        used += len(block)
    return "\n\n".join(blocks)


def _generate_answer(query: str, context: str, max_new_tokens: int):
    prompt = (
        "Answer the QUESTION using ONLY the SOURCE TEXT below.\n"
        "Write 1-2 sentences. Do NOT copy long passages.\n"
        "If the sources do not support an answer, output exactly: ABSTAIN\n\n"
        f"QUESTION: {query}\n\n"
        f"SOURCE TEXT:\n{context}\n\n"
        "ANSWER:"
    )

    inputs = _tokenizer(prompt, return_tensors="pt", truncation=True)
    with torch.no_grad():
        out = _gen_model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            num_beams=1,
            no_repeat_ngram_size=3,
        )
    ans = _tokenizer.decode(out[0], skip_special_tokens=True).strip()
    ans = _clean_answer(ans)
    return ans


app = FastAPI(title="Cited Notes Q&A", version="0.1")


@app.on_event("startup")
def startup():
    global _rows, _index, _embedder, _tokenizer, _gen_model

    _rows = _load_meta(META_FILE)
    _index = faiss.read_index(str(INDEX_FILE))

    _embedder = SentenceTransformer(EMBED_MODEL)

    _tokenizer = AutoTokenizer.from_pretrained(GEN_MODEL)
    _gen_model = AutoModelForSeq2SeqLM.from_pretrained(GEN_MODEL)
    _gen_model.eval()


@app.get("/health")
def health():
    ok = True
    ok = ok and (_rows is not None)
    ok = ok and (_index is not None)
    ok = ok and (_embedder is not None)
    ok = ok and (_tokenizer is not None)
    ok = ok and (_gen_model is not None)
    return {"ok": ok, "rows": 0 if _rows is None else len(_rows)}


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    retrieved = _retrieve(req.query, req.top_k)

    top_score = float(retrieved[0][0]) if len(retrieved) > 0 else 0.0
    if top_score < req.min_score:
        return AskResponse(
            query=req.query,
            abstained=True,
            answer="ABSTAIN",
            citations=[],
            top_chunks=[] if req.include_evidence else None,
        )

    context = _build_context(retrieved, req.max_context_chars)
    ans = _generate_answer(req.query, context, req.max_new_tokens)

    if ans == "ABSTAIN" or ans.strip() == "":
        return AskResponse(
            query=req.query,
            abstained=True,
            answer="ABSTAIN",
            citations=[],
            top_chunks=[] if req.include_evidence else None,
        )

    cite_k = req.cite_k
    if cite_k < 1:
        cite_k = 1
    if cite_k > len(retrieved):
        cite_k = len(retrieved)

    citations = []
    for j in range(cite_k):
        _, doc_id, chunk_id, _, _ = retrieved[j]
        citations.append(f"{doc_id}:{chunk_id}")

    top_chunks_out = None
    if req.include_evidence:
        top_chunks_out = []
        for score, doc_id, chunk_id, page, text in retrieved:
            top_chunks_out.append(
                ChunkOut(
                    score=float(score),
                    doc_id=str(doc_id),
                    chunk_id=str(chunk_id),
                    page=page if page is None else int(page),
                    text_preview=text[:220].replace("\n", " "),
                )
            )

    final_answer = ans + " " + " ".join([f"[{c}]" for c in citations])

    return AskResponse(
        query=req.query,
        abstained=False,
        answer=final_answer,
        citations=citations,
        top_chunks=top_chunks_out,
    )
