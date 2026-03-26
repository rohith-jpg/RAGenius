import re
import json
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple

import numpy as np
import faiss
import torch
from fastapi import FastAPI
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM


def load_meta(meta_file: Path) -> List[Dict[str, Any]]:
    rows = []
    with meta_file.open("r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s:
                continue
            rows.append(json.loads(s))
    return rows


def strip_citations(answer: str) -> str:
    out = []
    i = 0
    n = len(answer)
    while i < n:
        if answer[i] == "[":
            j = answer.find("]", i + 1)
            if j == -1:
                out.append(answer[i])
                i += 1
            else:
                i = j + 1
        else:
            out.append(answer[i])
            i += 1
    return "".join(out).strip()


def word_count(s: str) -> int:
    parts = [x for x in s.split() if x.strip() != ""]
    return len(parts)


def looks_like_sensitive_personal_info_query(q: str) -> bool:
    t = q.lower().strip()
    if "social security number" in t:
        return True
    if re.search(r"\bmy\s+ssn\b", t):
        return True
    if re.search(r"\bwhat\s+is\s+my\s+ssn\b", t):
        return True
    if re.search(r"\bwhat\s+is\s+my\s+social\s+security\b", t):
        return True
    return False


def extract_acronym_from_query(q: str) -> Optional[str]:
    t = q.strip()

    m = re.search(r"what\s+does\s+([A-Za-z0-9\-]{2,15})\s+stand\s+for", t, flags=re.IGNORECASE)
    if m:
        return m.group(1).strip()

    tokens = re.findall(r"\b[A-Z]{2,10}\b", t)
    if tokens:
        return tokens[0]
    return None


def find_expansion_in_text(acronym: str, text: str) -> Optional[str]:
    pat = re.compile(rf"([A-Za-z][A-Za-z \-/]{{3,120}})\(\s*{re.escape(acronym)}\s*\)")
    m = pat.search(text)
    if not m:
        return None
    phrase = m.group(1).strip()
    phrase = re.sub(r"\s+", " ", phrase)
    return phrase


def truncate_text(s: str, max_chars: int) -> str:
    if len(s) <= max_chars:
        return s
    return s[:max_chars].rstrip() + " ..."


def rerank_for_definition(query: str, retrieved: List[Tuple[float, str, str, int, str]]) -> List[Tuple[float, str, str, int, str]]:
    acronym = extract_acronym_from_query(query)
    if not acronym:
        return retrieved

    scored = []
    for score, doc_id, chunk_id, page, text in retrieved:
        bonus = 0.0
        if f"({acronym})" in text:
            bonus += 0.25
        if "stands for" in text.lower():
            bonus += 0.10
        scored.append((score + bonus, score, doc_id, chunk_id, page, text))

    scored.sort(key=lambda x: x[0], reverse=True)
    out = []
    for s2, score, doc_id, chunk_id, page, text in scored:
        out.append((score, doc_id, chunk_id, page, text))
    return out


app = FastAPI()

INDEX_FILE = Path("data/index/faiss.index")
META_FILE = Path("data/index/meta.jsonl")

EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
GEN_MODEL = "google/flan-t5-base"

rows: List[Dict[str, Any]] = []
index = None
embedder = None
tokenizer = None
gen_model = None


class AskRequest(BaseModel):
    query: str
    top_k: int = Field(default=10, ge=1, le=50)
    cite_k: int = Field(default=2, ge=1, le=10)
    include_evidence: bool = False
    min_score: float = 0.35
    max_context_chars: int = 6500
    max_chunk_chars: int = 900
    max_new_tokens: int = 220
    min_words: int = 8


@app.on_event("startup")
def startup():
    global rows, index, embedder, tokenizer, gen_model

    if not INDEX_FILE.exists():
        raise RuntimeError(f"Missing index file: {INDEX_FILE}")
    if not META_FILE.exists():
        raise RuntimeError(f"Missing meta file: {META_FILE}")

    rows = load_meta(META_FILE)
    index = faiss.read_index(str(INDEX_FILE))

    embedder = SentenceTransformer(EMBED_MODEL)

    tokenizer = AutoTokenizer.from_pretrained(GEN_MODEL)
    gen_model = AutoModelForSeq2SeqLM.from_pretrained(GEN_MODEL)
    gen_model.eval()


@app.get("/health")
def health():
    return {"ok": True, "rows": len(rows)}


@app.post("/ask")
def ask(req: AskRequest):
    q = req.query.strip()
    if len(q) == 0:
        return {"query": req.query, "abstained": True, "answer": "ABSTAIN", "citations": [], "top_chunks": []}

    if looks_like_sensitive_personal_info_query(q):
        return {"query": req.query, "abstained": True, "answer": "ABSTAIN", "citations": [], "top_chunks": []}

    qvec = embedder.encode([q], convert_to_numpy=True, normalize_embeddings=True)
    if qvec.dtype != np.float32:
        qvec = qvec.astype(np.float32)

    D, I = index.search(qvec, req.top_k)

    top_score = float(D[0][0])
    if top_score < req.min_score:
        return {"query": req.query, "abstained": True, "answer": "ABSTAIN", "citations": [], "top_chunks": []}

    retrieved = []
    allowed_cite = set()

    for j in range(req.top_k):
        idx = int(I[0][j])
        score = float(D[0][j])
        r = rows[idx]
        doc_id = r.get("doc_id", "")
        chunk_id = r.get("chunk_id", "")
        page = int(r.get("page", 0))
        text = r.get("text", "")
        key = f"{doc_id}:{chunk_id}"
        allowed_cite.add(key)
        retrieved.append((score, doc_id, chunk_id, page, text))

    retrieved = rerank_for_definition(q, retrieved)

    top_chunks = []
    for score, doc_id, chunk_id, page, text in retrieved:
        top_chunks.append({
            "score": score,
            "doc_id": doc_id,
            "chunk_id": chunk_id,
            "page": page,
            "text_preview": truncate_text(text.replace("\n", " "), 220),
        })

    acronym = extract_acronym_from_query(q)
    if acronym:
        for score, doc_id, chunk_id, page, text in retrieved:
            exp = find_expansion_in_text(acronym, text)
            if exp:
                base = f"{acronym} stands for {exp}."
                cites = [f"{doc_id}:{chunk_id}"]
                extra = []
                for s2, d2, c2, p2, t2 in retrieved:
                    k2 = f"{d2}:{c2}"
                    if k2 != cites[0]:
                        extra.append(k2)
                    if len(extra) >= (req.cite_k - 1):
                        break
                cites.extend(extra)
                answer = base + " " + " ".join([f"[{x}]" for x in cites])
                return {
                    "query": req.query,
                    "abstained": False,
                    "answer": answer.strip(),
                    "citations": cites,
                    "top_chunks": top_chunks if req.include_evidence else [],
                }

    context_blocks = []
    used_chars = 0
    for score, doc_id, chunk_id, page, text in retrieved:
        tshort = truncate_text(text, req.max_chunk_chars)
        block = f"SOURCE [{doc_id}:{chunk_id}] (page={page}): {tshort}"
        if used_chars + len(block) > req.max_context_chars:
            continue
        context_blocks.append(block)
        used_chars += len(block)

    context = "\n\n".join(context_blocks)

    prompt = (
        "You answer questions using ONLY the provided sources.\n"
        "Rules:\n"
        "1) If the sources do not contain the answer, output exactly: ABSTAIN\n"
        "2) Write a complete answer in 2-4 sentences.\n"
        "3) Prefer copying key terms exactly as written in sources.\n"
        "4) Do NOT answer with only a single word or only an acronym.\n\n"
        f"QUESTION: {q}\n\n"
        f"SOURCES:\n{context}\n\n"
        "ANSWER:"
    )

    def generate_once(p: str, max_new_tokens: int) -> str:
        inputs = tokenizer(p, return_tensors="pt", truncation=True)
        with torch.inference_mode():
            out = gen_model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                num_beams=4,
            )
        return tokenizer.decode(out[0], skip_special_tokens=True).strip()

    ans1 = generate_once(prompt, req.max_new_tokens)
    if ans1 == "ABSTAIN":
        return {"query": req.query, "abstained": True, "answer": "ABSTAIN", "citations": [], "top_chunks": top_chunks if req.include_evidence else []}

    wc1 = word_count(strip_citations(ans1))
    if wc1 < req.min_words:
        prompt2 = (
            prompt
            + "\n\nYour previous answer was too short.\n"
            + f"Rewrite the answer with at least {req.min_words} words, still using ONLY sources.\n"
            + "ANSWER:"
        )
        ans2 = generate_once(prompt2, max(req.max_new_tokens, 260))
        if ans2 != "ABSTAIN":
            ans1 = ans2

    answer_text = strip_citations(ans1)
    wc_final = word_count(answer_text)
    if wc_final < req.min_words:
        best = retrieved[0]
        score, doc_id, chunk_id, page, text = best
        snippet = truncate_text(text.replace("\n", " "), 260)
        forced = f"From the sources, {snippet}"
        ans1 = forced

    cites = []
    for score, doc_id, chunk_id, page, text in retrieved:
        key = f"{doc_id}:{chunk_id}"
        if key in allowed_cite:
            cites.append(key)
        if len(cites) >= req.cite_k:
            break

    answer = ans1.strip()
    if answer != "ABSTAIN":
        answer = answer + " " + " ".join([f"[{x}]" for x in cites])

    return {
        "query": req.query,
        "abstained": (answer.strip() == "ABSTAIN"),
        "answer": answer.strip(),
        "citations": cites if answer.strip() != "ABSTAIN" else [],
        "top_chunks": top_chunks if req.include_evidence else [],
    }
