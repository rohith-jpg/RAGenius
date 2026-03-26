# Doc RAG Agent

## Results (latest eval)

- **Overall pass rate:** **0.693** (52/75)
- **Doc Q&A pass rate:** **0.646** (42/65)
- **Should-abstain pass rate:** **1.000** (10/10)
- **Citation coverage (when answered):** **1.000** (65/65)
- **Abstain rate:** **0.133** (10/75)
- **Latency:** avg **7.387s**, p95 **30.230s**

**Full report:** `eval/report_v4.md`  
**Latest run log:** `eval/runs/v4.jsonl`

Local run Streamlit Demo: https://drive.google.com/file/d/1o09DW9fcFNbnMbcIqi_cRAVcaMA0ZuG-/view?usp=sharing


-------------------------------------------------------------------------------------------------------------------------

# Cited Notes Q&A (RAG with Citations + Abstain)

A Custom RAG app implemented from scratch: upload/keep a small set of PDFs/notes locally, ask questions, and get answers that **must include citations** to retrieved chunks — otherwise the system **abstains**.

## What it demonstrates
- Reliable retrieval (chunking + embeddings + vector search)
- Citation-gated answers (no citations → abstain)
- API service (FastAPI)
- UI (Streamlit)
- Measurable evaluation (75-task JSONL + report)

## Tech stack (resume keywords)
- Python
- Hugging Face Transformers
- sentence-transformers (embeddings)
- FAISS (vector search)
- FastAPI (API server)
- Streamlit (UI)
- PyMuPDF (PDF text extraction)

## Repo layout
- `rag/` chunking, indexing, search, answer-with-citations
- `app/` FastAPI server (`/health`, `/ask`)
- `ui/` Streamlit UI
- `eval/` questions + eval runner + markdown reports

## How it works (end-to-end)
1) PDFs are converted into plain text
2) Text is split into overlapping **chunks**
3) Each chunk is embedded into a vector
4) FAISS finds the closest chunk vectors to the question vector
5) The generator answers using only retrieved chunks
6) Output must include citations like `[doc_id:chunk_id]` or it abstains

## Quickstart (local)
### 0) Create venv + install
```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
1) Put PDFs here

Place PDFs in:

data/sample_docs/

2) Build chunks
python3 rag/build_chunks.py \
  --in_dir data/sample_docs \
  --out_file data/chunks/chunks.jsonl \
  --chunk_chars 2000 \
  --overlap_chars 300

3) Build FAISS index
python3 rag/build_index.py \
  --chunks_file data/chunks/chunks.jsonl \
  --out_dir data/index \
  --batch_size 64

4) Start API
python3 app/server.py


Test:

curl -s http://localhost:8000/health | python3 -m json.tool
curl -s -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"query":"What is ISCM?","top_k":10,"cite_k":2,"include_evidence":true}' \
  | python3 -m json.tool

5) Start UI
streamlit run ui/app.py

6) Run evaluation (75 tasks)
python3 eval/run_eval.py \
  --api http://localhost:8000 \
  --in_file eval/questions.jsonl \
  --out_run eval/runs/latest.jsonl \
  --out_report eval/report.md \
  --min_words 8 \
  --top_k 10 \
  --cite_k 2

Current eval snapshot (example)

75 tasks total

Citation coverage: 1.000 (when answered)

Pass rate: ~0.69 (varies by model + settings)

Common failure modes: too-short answers, keyword misses

Notes / limitations

Generator can produce short answers on some questions (improvable with prompt + model choice).

Retrieval quality depends on chunking + embedding model.
