# Eval Report

- Total tasks: **75**
- Overall pass rate: **0.693** (52/75)
- Abstain rate: **0.133** (10/75)
- Citation coverage (when answered): **1.000** (65/65)
- Latency avg: **7.387s**, p95: **30.230s**

## Per-category pass rate

| category | pass | total | rate |
|---|---:|---:|---:|
| doc_qa | 42 | 65 | 0.646 |
| should_abstain | 10 | 10 | 1.000 |

## Top failure modes

- **too_short_answer**: 17
- **keyword_miss**: 6

## Example failures (first 12)

- q005 (doc_qa): too_short_answer — What is meant by security status reporting in an ISCM program? — wc=7 — preview: `ISCM stands for Information Security Continuous Monitoring. [NIST.SP.800-137A:c0018] [NIST.SP.800-137A:c0001]`
- q006 (doc_qa): too_short_answer — What is ISCM program management about? — wc=7 — preview: `ISCM stands for Information Security Continuous Monitoring. [NIST.SP.800-137A:c0009] [NIST.SP.800-137A:c0114]`
- q007 (doc_qa): too_short_answer — What is the relationship between governance and ISCM? — wc=7 — preview: `ISCM stands for Information Security Continuous Monitoring. [NIST.SP.800-137A:c0009] [NIST.SP.800-137A:c0012]`
- q008 (doc_qa): keyword_miss — What are ISCM metrics used for? — wc=78 — preview: `to provide information in a context that is meaningful for each tier. For example, ISCM data collected at Tier 3 may be aggregated to provide security status or risk scores for a single system, for a collection of system`
- q012 (doc_qa): too_short_answer — What does ISCM encompass (people/policies/processes/tools)? — wc=7 — preview: `ISCM stands for Information Security Continuous Monitoring. [NIST.SP.800-137A:c0104] [NIST.SP.800-137A:c0029]`
- q013 (doc_qa): keyword_miss — What is the role of configuration management in continuous monitoring? — wc=22 — preview: `Controlling modifications to hardware, firmware, software, and documentation to protect the information system against improper modifications before, during, and after system implementation. [nistspecialpublication800-13`
- q016 (doc_qa): too_short_answer — What is the purpose of reviewing ISCM reports from common controls? — wc=7 — preview: `ISCM stands for Information Security Continuous Monitoring. [NIST.SP.800-137A:c0009] [nistspecialpublication800-137:c0040]`
- q018 (doc_qa): keyword_miss — What does remediation mean in the context of ISCM? — wc=28 — preview: `maturing measurement capabilities to increase visibility into assets and awareness of vulnerabilities, further enable data-driven control of the security of an organization’s information infrastructure, and increase orga`
- q020 (doc_qa): too_short_answer — What is meant by correlating security-related information in ISCM? — wc=7 — preview: `ISCM stands for Information Security Continuous Monitoring. [NIST.SP.800-137A:c0104] [nistspecialpublication800-137:c0159]`
- q025 (doc_qa): too_short_answer — What is the objective of an ISCM program assessment process? — wc=7 — preview: `ISCM stands for Information Security Continuous Monitoring. [NIST.SP.800-137A:c0009] [NIST.SP.800-137A:c0065]`
- q035 (doc_qa): keyword_miss — What does an ISCM program try to maintain over time? — wc=32 — preview: `From the sources, NIST SP 800-137A ASSESSING ISCM PROGRAMS: DEVELOPING AN ISCM PROGRAM ASSESSMENT 56 This publication is available free of charge from: https://doi.org/10.6028/NIST.SP.800-137A Figure 11 – ISCM Program Ma`
- q037 (doc_qa): too_short_answer — What is the difference between an ISCM strategy and an ISCM program? — wc=7 — preview: `ISCM stands for Information Security Continuous Monitoring. [NIST.SP.800-137A:c0009] [NIST.SP.800-137A:c0027]`
