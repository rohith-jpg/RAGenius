# Spec — Cited Notes Q&A (Phase 0)

## Goal
Answer questions over uploaded notes with **grounded citations**.
If the answer cannot be supported by retrieved chunks, the system **must abstain**.

## Input corpus
- 20–50 documents (PDF/MD/TXT)
- Stored locally under: data/sample_docs/

## Chunking contract
- Chunk size: 800–1200 tokens (or equivalent chars)
- Overlap: 150–200 tokens
- Each chunk must include metadata:
  - doc_id
  - source_name (file name)
  - page (PDF only, if available)
  - chunk_id
  - text

## Retrieval contract
- Vector search returns top_k = 5 chunks by default
- Each result includes:
  - doc_id, source_name, page, chunk_id, score, text

## Citation format (hard requirement)
- Every final answer must include at least **1 citation** in this exact format:
  - [doc_id:chunk_id]
- Recommended: cite per paragraph or per key claim.

## Abstain policy (hard requirement)
The app must return an abstain response if:
- no chunks are retrieved, OR
- top score is below threshold, OR
- the model cannot cite evidence for the answer
Abstain response template:
"I can’t find this in your uploaded notes. Please rephrase or upload the relevant document."

## UI requirements (Phase 0 statement)
- Single page UI: upload → build index → ask
- Show retrieved chunks panel (top 3–5) with doc/page/chunk_id

## Evaluation requirements (Phase 0 statement)
File: eval/questions.jsonl (~75)
- 50 answerable questions (should answer with citations)
- 25 unanswerable questions (should abstain)

Report: eval/report.md must include
- citation_coverage_percent
- abstain_rate_on_unanswerable
- false_answer_rate_on_unanswerable
- basic pass/fail per category

## Definition of Done (Phase 0)
- Repo has folder skeleton
- docs/spec.md defines citation + abstain contracts
- README exists
- eval/questions.jsonl placeholder exists
