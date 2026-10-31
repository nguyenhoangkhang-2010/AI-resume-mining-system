# Section detection on a synthetic multi-format CV corpus

Generated 2026-10-29 by `scripts/evaluate_sections.py` (seed 42).

- Documents: 96 PDFs (6 heading styles x 3 layouts x 2 languages, plus 24 documents with alternate heading wording)
- Body lines scored: 2735
- Regions that would call the LLM fallback: 205

Each body line has a known true section; a line is correct when the detector placed it in that section. The LLM fallback is disabled (stubbed), so this measures the deterministic stages only. The content is synthetic: results show sensitivity to layout and headings, not accuracy on real resumes. The heading lexicon was written around the "standard" wording, so those numbers are optimistic; "alternate" wording uses titles the lexicon was not designed around.

**Overall line accuracy: 0.116**

## Per section

| Section | Precision | Recall | F1 | Lines |
|---|---|---|---|---|
| certifications | 0.898 | 0.376 | 0.530 | 141 |
| education | 1.000 | 0.069 | 0.130 | 288 |
| experience | 0.000 | 0.000 | 0.000 | 1265 |
| personal_info | 0.954 | 0.323 | 0.482 | 384 |
| projects | 0.441 | 0.197 | 0.272 | 325 |
| skills | 0.475 | 0.331 | 0.390 | 172 |
| summary | 0.000 | 0.000 | 0.000 | 160 |

## By heading wording

| Heading wording | Line accuracy |
|---|---|
| alternate | 0.126 |
| standard | 0.113 |

## By heading style

| Heading style | Line accuracy |
|---|---|
| title_bold_large | 0.292 |
| title_bold_same | 0.028 |
| title_bold_tight | 0.021 |
| title_plain_gap | 0.032 |
| upper_large | 0.250 |
| upper_small | 0.024 |

## By layout

| Layout | Line accuracy |
|---|---|
| multi_page | 0.125 |
| single | 0.106 |
| two_column | 0.117 |

## By language

| Language | Line accuracy |
|---|---|
| en | 0.140 |
| vi | 0.092 |
