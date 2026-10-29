# Section detection on a synthetic multi-format CV corpus

Generated 2026-10-29 by `scripts/evaluate_sections.py` (seed 42).

- Documents: 96 PDFs (6 heading styles x 3 layouts x 2 languages, plus 24 documents with alternate heading wording)
- Body lines scored: 2735
- Regions that would call the LLM fallback: 54

Each body line has a known true section; a line is correct when the detector placed it in that section. The LLM fallback is disabled (stubbed), so this measures the deterministic stages only. The content is synthetic: results show sensitivity to layout and headings, not accuracy on real resumes. The heading lexicon was written around the "standard" wording, so those numbers are optimistic; "alternate" wording uses titles the lexicon was not designed around.

**Overall line accuracy: 0.807**

## Per section

| Section | Precision | Recall | F1 | Lines |
|---|---|---|---|---|
| certifications | 1.000 | 0.858 | 0.924 | 141 |
| education | 1.000 | 0.740 | 0.850 | 288 |
| experience | 0.997 | 0.753 | 0.858 | 1265 |
| personal_info | 0.997 | 1.000 | 0.999 | 384 |
| projects | 0.929 | 0.803 | 0.861 | 325 |
| skills | 0.716 | 0.907 | 0.800 | 172 |
| summary | 1.000 | 0.750 | 0.857 | 160 |

## By heading wording

| Heading wording | Line accuracy |
|---|---|
| alternate | 0.254 |
| standard | 0.994 |

## By heading style

| Heading style | Line accuracy |
|---|---|
| title_bold_large | 0.988 |
| title_bold_same | 0.594 |
| title_bold_tight | 0.991 |
| title_plain_gap | 1.000 |
| upper_large | 0.648 |
| upper_small | 1.000 |

## By layout

| Layout | Line accuracy |
|---|---|
| multi_page | 0.790 |
| single | 0.823 |
| two_column | 0.807 |

## By language

| Language | Line accuracy |
|---|---|
| en | 0.805 |
| vi | 0.809 |
