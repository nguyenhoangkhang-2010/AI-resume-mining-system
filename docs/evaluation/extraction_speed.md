# Extraction speed

Generated 2026-10-31 by `scripts/benchmark_extraction.py` (seed 42, English synthetic CVs, local GGUF model on CPU).

## Rules first + instructions read once (final)

- Documents: 4
- Seconds per CV: mean 42, min 4, max 83
- LLM calls per CV: 3.8

### Where the time goes (mean seconds per CV)

| Stage | Seconds | LLM calls | LLM seconds |
|---|---|---|---|
| sections (parse, layout, headings) | 17.4 | 3.2 | 17.2 |
| personal_info | 0.2 | 0.0 | 0.0 |
| summary | 0.0 | 0.0 | 0.0 |
| education | 0.0 | 0.0 | 0.0 |
| experience | 0.0 | 0.0 | 0.0 |
| projects | 0.0 | 0.0 | 0.0 |
| certifications | 22.2 | 0.5 | 22.2 |
| skills | 1.7 | 0.0 | 0.0 |

### Sections read by rules or by the model

| Section | Rules | Model |
|---|---|---|
| certifications | 2 | 2 |
| education | 4 | 0 |
| experience | 4 | 0 |
| projects | 4 | 0 |
| summary | 4 | 0 |

### Fields found (micro-averaged over the documents)

| Field | Precision | Recall | F1 | Expected | Found |
|---|---|---|---|---|---|
| name | 1.000 | 1.000 | 1.000 | 4 | 4 |
| companies | 1.000 | 1.000 | 1.000 | 9 | 10 |
| roles | 1.000 | 1.000 | 1.000 | 7 | 7 |
| schools | 1.000 | 1.000 | 1.000 | 4 | 4 |
| degrees | 1.000 | 1.000 | 1.000 | 4 | 4 |
| skills | 0.153 | 0.458 | 0.229 | 24 | 72 |
| certifications | 1.000 | 0.800 | 0.889 | 5 | 4 |

