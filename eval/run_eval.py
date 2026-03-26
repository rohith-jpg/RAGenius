import argparse
import json
import time
from collections import defaultdict, Counter
from pathlib import Path

import requests


def read_jsonl(path: Path):
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows):
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def contains_any(text: str, keywords):
    t = text.lower()
    for k in keywords:
        if k.lower() in t:
            return True
    return False


def strip_citations(answer: str):
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


def word_count(s: str):
    parts = [x for x in s.split() if x.strip() != ""]
    return len(parts)


def percentile(values, p):
    if len(values) == 0:
        return 0.0
    v = sorted(values)
    if p <= 0:
        return float(v[0])
    if p >= 100:
        return float(v[-1])
    k = (len(v) - 1) * (p / 100.0)
    f = int(k)
    c = f + 1
    if c >= len(v):
        return float(v[f])
    d0 = v[f] * (c - k)
    d1 = v[c] * (k - f)
    return float(d0 + d1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--api", default="http://localhost:8000")
    ap.add_argument("--in_file", default="eval/questions.jsonl")
    ap.add_argument("--out_run", default="eval/runs/latest.jsonl")
    ap.add_argument("--out_report", default="eval/report.md")
    ap.add_argument("--sleep_ms", type=int, default=0)

    ap.add_argument("--top_k", type=int, default=10)
    ap.add_argument("--cite_k", type=int, default=2)
    ap.add_argument("--include_evidence", action="store_true")

    ap.add_argument("--min_words", type=int, default=8)
    ap.add_argument("--timeout_sec", type=int, default=120)
    ap.add_argument("--fail_examples", type=int, default=12)
    args = ap.parse_args()

    tasks = read_jsonl(Path(args.in_file))

    run_rows = []
    fail_modes = Counter()

    totals = 0
    passed = 0

    cat_tot = defaultdict(int)
    cat_pass = defaultdict(int)

    answered_cnt = 0
    answered_with_cites = 0
    abstain_cnt = 0

    latencies = []

    for t in tasks:
        tid = t["id"]
        cat = t.get("category", "unknown")
        q = t["query"]
        must_abstain = bool(t.get("must_abstain", False))
        expect_any_of = t.get("expect_any_of", None)

        top_k = int(t.get("top_k", args.top_k))
        cite_k = int(t.get("cite_k", args.cite_k))

        payload = {
            "query": q,
            "top_k": top_k,
            "cite_k": cite_k,
            "include_evidence": bool(args.include_evidence),
        }

        t0 = time.time()
        http_ok = True
        http_status = 0
        err = ""

        try:
            r = requests.post(args.api + "/ask", json=payload, timeout=args.timeout_sec)
            http_status = int(r.status_code)
            out = r.json()
        except Exception as e:
            http_ok = False
            out = {}
            err = str(e)

        dt = time.time() - t0
        latencies.append(dt)

        abstained = bool(out.get("abstained", False))
        answer = out.get("answer", "")
        citations = out.get("citations", [])

        totals += 1
        cat_tot[cat] += 1

        answer_stripped = strip_citations(answer)
        wc = word_count(answer_stripped)

        if abstained or answer_stripped == "ABSTAIN":
            abstain_cnt += 1
        else:
            answered_cnt += 1
            if isinstance(citations, list) and len(citations) > 0:
                answered_with_cites += 1

        ok = True
        reason = "ok"

        if not http_ok or http_status >= 400:
            ok = False
            reason = "http_error"
            fail_modes[reason] += 1
        else:
            if must_abstain:
                if not (abstained or answer_stripped == "ABSTAIN"):
                    ok = False
                    reason = "should_abstain_but_answered"
                    fail_modes[reason] += 1
            else:
                if abstained or answer_stripped == "ABSTAIN":
                    ok = False
                    reason = "abstained_unexpectedly"
                    fail_modes[reason] += 1
                else:
                    if not isinstance(citations, list) or len(citations) == 0:
                        ok = False
                        reason = "missing_citations"
                        fail_modes[reason] += 1
                    if ok and wc < args.min_words:
                        ok = False
                        reason = "too_short_answer"
                        fail_modes[reason] += 1
                    if ok and expect_any_of is not None:
                        if not contains_any(answer_stripped, expect_any_of):
                            ok = False
                            reason = "keyword_miss"
                            fail_modes[reason] += 1

        if ok:
            passed += 1
            cat_pass[cat] += 1

        run_rows.append({
            "id": tid,
            "category": cat,
            "query": q,
            "must_abstain": must_abstain,
            "passed": ok,
            "reason": reason,
            "latency_sec": dt,
            "http_ok": http_ok,
            "http_status": http_status,
            "error": err,
            "abstained": abstained,
            "citations": citations,
            "word_count": wc,
            "top_k": top_k,
            "cite_k": cite_k,
            "answer_preview": answer[:220]
        })

        if args.sleep_ms > 0:
            time.sleep(args.sleep_ms / 1000.0)

    Path(args.out_run).parent.mkdir(parents=True, exist_ok=True)
    write_jsonl(Path(args.out_run), run_rows)

    citation_coverage = 0.0
    if answered_cnt > 0:
        citation_coverage = answered_with_cites / answered_cnt

    abstain_rate = abstain_cnt / totals if totals > 0 else 0.0
    pass_rate = passed / totals if totals > 0 else 0.0

    lat_avg = sum(latencies) / len(latencies) if len(latencies) > 0 else 0.0
    lat_p95 = percentile(latencies, 95)

    lines = []
    lines.append("# Eval Report")
    lines.append("")
    lines.append(f"- Total tasks: **{totals}**")
    lines.append(f"- Overall pass rate: **{pass_rate:.3f}** ({passed}/{totals})")
    lines.append(f"- Abstain rate: **{abstain_rate:.3f}** ({abstain_cnt}/{totals})")
    lines.append(f"- Citation coverage (when answered): **{citation_coverage:.3f}** ({answered_with_cites}/{answered_cnt})")
    lines.append(f"- Latency avg: **{lat_avg:.3f}s**, p95: **{lat_p95:.3f}s**")
    lines.append("")
    lines.append("## Per-category pass rate")
    lines.append("")
    lines.append("| category | pass | total | rate |")
    lines.append("|---|---:|---:|---:|")
    for cat in sorted(cat_tot.keys()):
        tot = cat_tot[cat]
        pas = cat_pass.get(cat, 0)
        rate = pas / tot if tot > 0 else 0.0
        lines.append(f"| {cat} | {pas} | {tot} | {rate:.3f} |")
    lines.append("")
    lines.append("## Top failure modes")
    lines.append("")
    for k, v in fail_modes.most_common(10):
        lines.append(f"- **{k}**: {v}")
    lines.append("")
    lines.append(f"## Example failures (first {args.fail_examples})")
    lines.append("")
    shown = 0
    for r in run_rows:
        if not r["passed"]:
            lines.append(
                f"- {r['id']} ({r['category']}): {r['reason']} — {r['query']} — wc={r['word_count']} — preview: `{r['answer_preview']}`"
            )
            shown += 1
            if shown >= args.fail_examples:
                break
    lines.append("")
    Path(args.out_report).write_text("\n".join(lines), encoding="utf-8")

    print(f"wrote: {args.out_run}")
    print(f"wrote: {args.out_report}")
    print(f"overall_pass_rate={pass_rate:.3f}")
    print(f"citation_coverage={citation_coverage:.3f}")
    print(f"abstain_rate={abstain_rate:.3f}")
    print(f"lat_avg={lat_avg:.3f}")
    print(f"lat_p95={lat_p95:.3f}")


if __name__ == "__main__":
    main()
