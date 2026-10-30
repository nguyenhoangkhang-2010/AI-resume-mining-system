# Section detection on synthetic multi-format CV corpora

Generated 2026-10-30 by `scripts/evaluate_sections.py` (seeds 42/42).

Each body line has a known true section; a line is correct when the detector placed it in that section (lines of sections that are not extracted, such as references or interests, are correct when dropped). The LLM is asked only about unfamiliar headings (answers are cached); every other LLM fallback is stubbed. The content is synthetic: results show sensitivity to layout and headings, not accuracy on real resumes. The heading lexicon and the example headings of the heading classifier were written by the same author as the corpora; "standard" wording is what the lexicon was built around, "alternate" and "industry" wording were chosen to be different from it.

LLM heading calls: 60 (261 s in total)

## Effect of each stage

Line accuracy by heading wording, adding one stage at a time. "alternate" (base corpus) and "industry" (industries corpus) are headings the lexicon was not built around.

| Configuration | Base standard | Base alternate | Industries standard | Industries industry |
|---|---|---|---|---|
| words only (lexicon) | 0.994 | 0.254 | 0.933 | 0.576 |
| + heading style | 0.994 | 0.292 | 0.943 | 0.614 |
| + heading classifier (+ LLM with --heading-llm) | 0.994 | 0.721 | 0.997 | 0.960 |

## Base corpus, final configuration (6 heading styles, 3 layouts, 2 languages; LLM fallback regions: 10)

- Documents: 96 PDFs, 2735 body lines scored
- **Overall line accuracy: 0.925**

### Per section

| Section | Precision | Recall | F1 | Lines |
|---|---|---|---|---|
| certifications | 1.000 | 0.950 | 0.975 | 141 |
| education | 1.000 | 0.990 | 0.995 | 288 |
| experience | 0.988 | 0.874 | 0.927 | 1265 |
| personal_info | 1.000 | 1.000 | 1.000 | 384 |
| projects | 0.978 | 0.963 | 0.971 | 325 |
| skills | 0.933 | 0.971 | 0.952 | 172 |
| summary | 0.470 | 0.887 | 0.615 | 160 |

### By heading wording

| Heading wording | Line accuracy |
|---|---|
| alternate | 0.721 |
| standard | 0.994 |

### By heading style

| Heading style | Line accuracy |
|---|---|
| title_bold_large | 0.988 |
| title_bold_same | 0.855 |
| title_bold_tight | 0.991 |
| title_plain_gap | 1.000 |
| upper_large | 0.857 |
| upper_small | 1.000 |

### By layout

| Layout | Line accuracy |
|---|---|
| multi_page | 0.902 |
| single | 0.933 |
| two_column | 0.935 |

### By language

| Language | Line accuracy |
|---|---|
| en | 0.869 |
| vi | 0.980 |

## Industries corpus, final configuration (6 industries, 6 layouts, 2 languages; LLM fallback regions: 16)

- Documents: 144 PDFs, 5451 body lines scored
- **Overall line accuracy: 0.978**

### Per section

| Section | Precision | Recall | F1 | Lines |
|---|---|---|---|---|
| certifications | 0.998 | 0.977 | 0.987 | 472 |
| education | 0.990 | 0.910 | 0.948 | 432 |
| experience | 0.996 | 1.000 | 0.998 | 1951 |
| other | 1.000 | 0.993 | 0.996 | 986 |
| personal_info | 1.000 | 1.000 | 1.000 | 576 |
| projects | 0.995 | 0.986 | 0.991 | 426 |
| skills | 0.974 | 0.882 | 0.925 | 380 |
| summary | 0.986 | 0.952 | 0.969 | 228 |

### By heading wording

| Heading wording | Line accuracy |
|---|---|
| industry | 0.960 |
| standard | 0.997 |

### By layout

| Layout | Line accuracy |
|---|---|
| banner_two_column | 0.966 |
| long | 0.990 |
| sidebar_right | 0.982 |
| single | 0.977 |
| timeline | 0.983 |
| two_column | 0.968 |

### By industry

| Industry | Line accuracy |
|---|---|
| education | 0.990 |
| finance | 0.985 |
| healthcare | 0.979 |
| marketing | 0.971 |
| mechanical | 0.961 |
| software | 0.983 |

### By language

| Language | Line accuracy |
|---|---|
| en | 0.980 |
| vi | 0.977 |

