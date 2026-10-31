# Section detection on synthetic multi-format CV corpora

Generated 2026-10-31 by `scripts/evaluate_sections.py` (seeds 42/42).

Each body line has a known true section; a line is correct when the detector placed it in that section (lines of sections that are not extracted, such as references or interests, are correct when dropped). The LLM fallback is stubbed (always "other"), so this measures the deterministic stages and the embedding models only. The content is synthetic: results show sensitivity to layout and headings, not accuracy on real resumes. The heading lexicon and the example headings of the heading classifier were written by the same author as the corpora; "standard" wording is what the lexicon was built around, "alternate" and "industry" wording were chosen to be different from it.

## Effect of each stage

Line accuracy by heading wording, adding one stage at a time. "alternate" (base corpus) and "industry" (industries corpus) are headings the lexicon was not built around.

| Configuration | Base standard | Base alternate | Industries standard | Industries industry |
|---|---|---|---|---|
| words only (lexicon) | 0.994 | 0.254 | 0.924 | 0.573 |
| + heading style | 0.994 | 0.292 | 0.943 | 0.614 |
| + heading classifier (+ LLM with --heading-llm) | 0.994 | 0.608 | 0.941 | 0.783 |

## Base corpus, final configuration (6 heading styles, 3 layouts, 2 languages; LLM fallback regions: 42)

- Documents: 96 PDFs, 2735 body lines scored
- **Overall line accuracy: 0.897**

### Per section

| Section | Precision | Recall | F1 | Lines |
|---|---|---|---|---|
| certifications | 1.000 | 0.922 | 0.959 | 141 |
| education | 1.000 | 0.740 | 0.850 | 288 |
| experience | 0.978 | 0.909 | 0.942 | 1265 |
| personal_info | 0.975 | 1.000 | 0.987 | 384 |
| projects | 0.937 | 0.868 | 0.901 | 325 |
| skills | 0.708 | 0.971 | 0.819 | 172 |
| summary | 1.000 | 0.787 | 0.881 | 160 |

### By heading wording

| Heading wording | Line accuracy |
|---|---|
| alternate | 0.608 |
| standard | 0.994 |

### By heading style

| Heading style | Line accuracy |
|---|---|
| title_bold_large | 0.988 |
| title_bold_same | 0.830 |
| title_bold_tight | 0.991 |
| title_plain_gap | 1.000 |
| upper_large | 0.770 |
| upper_small | 1.000 |

### By layout

| Layout | Line accuracy |
|---|---|
| multi_page | 0.895 |
| single | 0.881 |
| two_column | 0.908 |

### By language

| Language | Line accuracy |
|---|---|
| en | 0.916 |
| vi | 0.877 |

## Industries corpus, final configuration (6 industries, 6 layouts, 2 languages; LLM fallback regions: 88)

- Documents: 144 PDFs, 5451 body lines scored
- **Overall line accuracy: 0.860**

### Per section

| Section | Precision | Recall | F1 | Lines |
|---|---|---|---|---|
| certifications | 0.998 | 0.966 | 0.982 | 472 |
| education | 0.678 | 0.931 | 0.784 | 432 |
| experience | 0.989 | 0.889 | 0.936 | 1951 |
| other | 1.000 | 0.692 | 0.818 | 986 |
| personal_info | 0.990 | 1.000 | 0.995 | 576 |
| projects | 0.539 | 0.770 | 0.634 | 426 |
| skills | 0.888 | 0.789 | 0.836 | 380 |
| summary | 0.986 | 0.921 | 0.952 | 228 |

### By heading wording

| Heading wording | Line accuracy |
|---|---|
| industry | 0.783 |
| standard | 0.941 |

### By layout

| Layout | Line accuracy |
|---|---|
| banner_two_column | 0.853 |
| long | 0.908 |
| sidebar_right | 0.839 |
| single | 0.850 |
| timeline | 0.863 |
| two_column | 0.827 |

### By industry

| Industry | Line accuracy |
|---|---|
| education | 0.682 |
| finance | 0.909 |
| healthcare | 0.896 |
| marketing | 0.871 |
| mechanical | 0.927 |
| software | 0.882 |

### By language

| Language | Line accuracy |
|---|---|
| en | 0.868 |
| vi | 0.852 |

