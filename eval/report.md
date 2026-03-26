# Eval Report

- Total tasks: **75**
- Overall pass rate: **0.653** (49/75)
- Abstain rate: **0.120** (9/75)
- Citation coverage (when answered): **1.000** (66/66)

## Per-category pass rate

| category | pass | total | rate |
|---|---:|---:|---:|
| doc_qa | 40 | 65 | 0.615 |
| should_abstain | 9 | 10 | 0.900 |

## Top failure modes

- **keyword_miss**: 25
- **should_abstain_but_answered**: 1

## Example failures (first 10)

- q002 (doc_qa): keyword_miss — What does ISCM stand for? — preview: `ISCM [nistspecialpublication800-137:c0040] [nistspecialpublication800-137:c0159]`
- q003 (doc_qa): keyword_miss — What is the purpose of an ISCM strategy? — preview: `organization-wide application of ISCM [nistspecialpublication800-137:c0159] [nistspecialpublication800-137:c0040]`
- q004 (doc_qa): keyword_miss — What activities are mentioned as part of implementing an ISCM strategy? — preview: `ISCM controls, and the deployment of ISCM systems [nistspecialpublication800-137:c0040] [nistspecialpublication800-137:c0159]`
- q007 (doc_qa): keyword_miss — What is the relationship between governance and ISCM? — preview: `ISCM [NIST.SP.800-137A:c0012] [NIST.SP.800-137A:c0036]`
- q008 (doc_qa): keyword_miss — What are ISCM metrics used for? — preview: `Information systems [NIST.SP.800-137A:c0122] [NIST.SP.800-137A:c0012]`
- q009 (doc_qa): keyword_miss — In ISCM, what kinds of stakeholders consume monitoring information? — preview: `individuals [nistspecialpublication800-137:c0159] [nistspecialpublication800-137:c0072]`
- q016 (doc_qa): keyword_miss — What is the purpose of reviewing ISCM reports from common controls? — preview: `Tier 3 officials [nistspecialpublication800-137:c0040] [NIST.SP.800-137A:c0116]`
- q017 (doc_qa): keyword_miss — What is the purpose of maintaining system authorization in ISCM? — preview: `OA [nistspecialpublication800-137:c0040] [NIST.SP.800-137A:c0038]`
- q018 (doc_qa): keyword_miss — What does remediation mean in the context of ISCM? — preview: `resilience [NIST.SP.800-88r2:c0029] [nistspecialpublication800-137:c0040]`
- q021 (doc_qa): keyword_miss — What are typical outputs of an ISCM program? — preview: `https://doi.org/10.6028/NIST.SP.800-137A Figure 11 – ISCM Program Management Traceability Chain ID: NIST. SP.800–137A:c0122 TEXT: Nist SP 800-137A ASSESSING ISCM PROGRAMS: DEVELOPING AN ISCM PREPARATION ASSECTION ASSELLI`
