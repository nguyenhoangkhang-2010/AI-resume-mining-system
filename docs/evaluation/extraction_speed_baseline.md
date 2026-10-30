# Extraction speed

Generated 2026-10-31 by `scripts/benchmark_extraction.py` (English synthetic CVs (seed 42), local GGUF model on CPU).

## Before: rules off, instruction cache off

- Documents: 4
- Seconds per CV: mean 407, min 327, max 507
- LLM calls per CV: 8.2

### Where the time goes (mean seconds per CV)

| Stage | Seconds | LLM calls | LLM seconds |
|---|---|---|---|
| sections (parse, layout, headings) | 32.0 | 3.2 | 31.9 |
| personal_info | 0.2 | 0.0 | 0.0 |
| summary | 33.6 | 1.0 | 33.6 |
| education | 50.5 | 1.0 | 50.5 |
| experience | 100.5 | 1.0 | 100.5 |
| projects | 129.1 | 1.0 | 129.1 |
| certifications | 59.6 | 1.0 | 59.6 |
| skills | 1.2 | 0.0 | 0.0 |

### Fields found (micro-averaged over the documents)

| Field | Precision | Recall | F1 | Expected | Found |
|---|---|---|---|---|---|
| name | 1.000 | 1.000 | 1.000 | 4 | 4 |
| companies | 1.000 | 0.111 | 0.200 | 9 | 1 |
| roles | 1.000 | 0.143 | 0.250 | 7 | 1 |
| schools | 1.000 | 1.000 | 1.000 | 4 | 4 |
| degrees | 0.167 | 0.500 | 0.250 | 4 | 12 |
| skills | 0.153 | 0.458 | 0.229 | 24 | 72 |
| certifications | 1.000 | 0.800 | 0.889 | 5 | 4 |

