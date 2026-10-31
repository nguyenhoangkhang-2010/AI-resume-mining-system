# Extraction quality: what changed on this branch

| Change | Where | Evidence |
|---|---|---|
| Confidence score per CV, with reasons | [app/services/confidence.py](../../app/services/confidence.py), `confidence` in the resume API | [confidence.md](confidence.md) |
| French, Spanish, German, Portuguese, Russian vocabulary; non-Latin scripts survive normalisation; headings as data | [vocabulary files](../../app/extraction/rules/vocabulary/), [heading_lexicon.py](../../app/extraction/section/heading_lexicon.py) | [multilingual_README.md](multilingual_README.md) |
| PNG/JPEG uploads (when OCR is on), converted to an A4 page and read like a scanned PDF | [image_parser.py](../../app/resume_processing/parsers/image_parser.py) | unit tests; OCR itself untested (no Tesseract here) |
| Degrees are matched by kind ("Bachelor" = "Bachelor of Science in X") in the evaluation | [field_eval.py](../../app/evaluation/field_eval.py) | tests; fixes a metric artifact, not the extractor |
| Regions with no heading and no confident answer are placed under the heading above them in the same column | `SectionDetector._below_heading` | below |

## Column placement (designed templates)

A designed CV can split one section into several regions (job titles in a
narrow box, descriptions in a wide one). A region the text classifier and the
model cannot place was dropped. It now joins the section of the closest heading
above it in the same column, only when both are unsure, so confident answers
and cross-page continuation are unchanged.

On the real CV that showed it, experience went from 2 detected lines to 30.
Across the sets (rules only, no language model):

| Measure | Before | After |
|---|---|---|
| synthetic section lines, final configuration (4 corpora columns) | 0.994 / 0.608 / 0.941 / 0.783 | 0.994 / 0.608 / 0.941 / 0.783 |
| synthetic, lexicon only, industries standard | 0.933 | 0.924 |
| 9 real CVs, core entity F1 | 0.455 [0.164, 0.741] | 0.482 [0.186, 0.759] |
| real CVs, companies / roles recall | 0.294 / 0.368 | 0.353 / 0.421 |

The real-CV change is inside the interval and the lexicon-only synthetic row
loses 0.009, so this is a small gain on one layout family, not a general
improvement. The rule can also put footer text under a section when a heading
precedes it in the same column; such a section is scored 0.7 for structure (`sections` in the
confidence), below one found by its heading.

## Not done

- Tesseract is not installed on the development machine: OCR for scans and
  photos was not run, only the conversion to a page.
- Skills precision (about 0.1 on real CVs) and recall (0.33) are unchanged.
- No new real CVs were available, so nothing here is validated on languages
  other than English beyond the invented set.
