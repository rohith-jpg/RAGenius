# Eval Report

- Total tasks: **75**
- Overall pass rate: **0.493** (37/75)
- Abstain rate: **0.120** (9/75)
- Citation coverage (when answered): **1.000** (66/66)
- Latency avg: **2.074s**, p95: **7.826s**

## Per-category pass rate

| category | pass | total | rate |
|---|---:|---:|---:|
| doc_qa | 28 | 65 | 0.431 |
| should_abstain | 9 | 10 | 0.900 |

## Top failure modes

- **too_short_answer**: 32
- **keyword_miss**: 5
- **should_abstain_but_answered**: 1

## Example failures (first 12)

- q002 (doc_qa): too_short_answer — What does ISCM stand for? — wc=1 — preview: `ISCM [nistspecialpublication800-137:c0040] [nistspecialpublication800-137:c0159]`
- q003 (doc_qa): too_short_answer — What is the purpose of an ISCM strategy? — wc=4 — preview: `organization-wide application of ISCM [nistspecialpublication800-137:c0159] [nistspecialpublication800-137:c0040]`
- q004 (doc_qa): keyword_miss — What activities are mentioned as part of implementing an ISCM strategy? — wc=8 — preview: `ISCM controls, and the deployment of ISCM systems [nistspecialpublication800-137:c0040] [nistspecialpublication800-137:c0159]`
- q006 (doc_qa): too_short_answer — What is ISCM program management about? — wc=3 — preview: `ISCM program management. [NIST.SP.800-137A:c0114] [nistspecialpublication800-137:c0040]`
- q007 (doc_qa): too_short_answer — What is the relationship between governance and ISCM? — wc=1 — preview: `ISCM [NIST.SP.800-137A:c0012] [NIST.SP.800-137A:c0036]`
- q008 (doc_qa): too_short_answer — What are ISCM metrics used for? — wc=2 — preview: `Information systems [NIST.SP.800-137A:c0122] [NIST.SP.800-137A:c0012]`
- q009 (doc_qa): too_short_answer — In ISCM, what kinds of stakeholders consume monitoring information? — wc=1 — preview: `individuals [nistspecialpublication800-137:c0159] [nistspecialpublication800-137:c0072]`
- q010 (doc_qa): too_short_answer — What kinds of information are presented in ISCM reports? — wc=2 — preview: `security-related information [NIST.SP.800-137A:c0123] [nistspecialpublication800-137:c0160]`
- q014 (doc_qa): too_short_answer — What does it mean to collect and analyze relevant security metrics? — wc=5 — preview: `Data collection, analysis and reporting [nistspecialpublication800-100:c0294] [nistspecialpublication800-137:c0061]`
- q016 (doc_qa): too_short_answer — What is the purpose of reviewing ISCM reports from common controls? — wc=3 — preview: `Tier 3 officials [nistspecialpublication800-137:c0040] [NIST.SP.800-137A:c0116]`
- q017 (doc_qa): too_short_answer — What is the purpose of maintaining system authorization in ISCM? — wc=1 — preview: `OA [nistspecialpublication800-137:c0040] [NIST.SP.800-137A:c0038]`
- q018 (doc_qa): too_short_answer — What does remediation mean in the context of ISCM? — wc=1 — preview: `resilience [NIST.SP.800-88r2:c0029] [nistspecialpublication800-137:c0040]`
