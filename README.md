# RAGenius — AI‑Powered Document Q&A System (Custom RAG with Citations + Abstain)

RAGenius is a lightweight Retrieval‑Augmented Generation (RAG) system that answers questions from PDF documents using verified citations. It retrieves relevant chunks, generates answers only when evidence exists, and abstains when support is missing.

## ✨ Features
- Custom RAG pipeline (chunking + embeddings + FAISS vector search)
- Citation‑gated answering with abstain logic
- FastAPI backend for retrieval and generation
- Streamlit UI for interactive Q&A
- Evaluation using a 75‑task JSONL benchmark

## 🚀 How to Run (Local Setup)

### 1. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt

### 2. Add PDFs
Place your documents in:
data/sample_docs/

### 3. Build chunks
python3 rag/build_chunks.py \
  --in_dir data/sample_docs \
  --out_file data/chunks/chunks.jsonl \
  --chunk_chars 2000 \
  --overlap_chars 300

### 4. Build FAISS index
python3 rag/build_index.py \
  --chunks_file data/chunks/chunks.jsonl \
  --out_dir data/index \
  --batch_size 64

### 5. Start the API
python3 app/server.py

### 6. Start the UI
streamlit run ui/app.py

### 7. Run evaluation (optional)
python3 eval/run_eval.py \
  --api http://localhost:8000 \
  --in_file eval/questions.jsonl \
  --out_run eval/runs/latest.jsonl \
  --out_report eval/report.md \
  --min_words 8 \
  --top_k 10 \
  --cite_k 2

## 📁 Project Structure
app/            # FastAPI backend
rag/            # RAG logic (chunking, embeddings, retrieval)
data/           # Sample PDFs and chunk outputs
ui/             # Streamlit UI
eval/           # Evaluation tasks, logs, and reports
docs/           # Additional documentation

## 🧠 Tech Stack
Python, FastAPI, Hugging Face Transformers, Sentence‑Transformers, FAISS, Streamlit, PyMuPDF

## 📊 Evaluation (latest)
- Overall pass rate: 0.693 (52/75)
- Doc Q&A pass rate: 0.646 (42/65)
- Should‑abstain pass rate: 1.000 (10/10)
- Citation coverage: 1.000 (65/65)
- Latency: avg 7.38s

Full report: eval/report_v4.md  
Latest run log: eval/runs/v4.jsonl

## 🚀 Quickstart (Local)
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

  ## 🔮 Future Improvements
- Add support for multiple embedding models
- Improve long‑context answer generation
- Add PDF preview inside the UI
- Add Docker support for easy deployment
- Add GPU acceleration for faster indexing
- Add a hosted demo link



