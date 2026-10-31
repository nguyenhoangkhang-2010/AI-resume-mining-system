# How far can an extracted CV be trusted?

The system cannot be right about every CV, whatever the language, field or
layout. What it can do is say which extractions to read twice. Every processed
CV now carries a `confidence` ([schema](../api.md)): a score from 0 to 1, a
level (`high` from 0.9, `medium` from 0.5, otherwise `low`), the four
components behind it and short reasons for what lowered it.

## What the score is made of

All of it is observed by the pipeline itself; no extra model runs
([confidence.py](../../app/services/confidence.py)).

| Component (weight) | Looks at |
|---|---|
| completeness (0.35) | name, contact, experience, education, skills present |
| structure (0.25) | how each section that produced entries was found: a heading the CV spells out or learned from its look counts most, a classifier's guess less, a model's guess least; a section placed only by its position under a heading counts in between |
| extraction (0.20) | for experience and education, whether the rules or the language model produced the entries (rules only accept what has the expected shape) |
| fields (0.20) | entries have company/title/dates/institution, their values are the size of a name and hold no year, and the date ranges written in the CV are matched by entries (four ranges in the text and one dated job means jobs were lost) |

Text read by OCR multiplies the score by 0.85 and a CV with almost no text by
0.8. The signals are recorded while the CV is processed: how each section was
found (`SectionDetector`), which extractors used rules or the model (a
per-document counter next to the global one), and which pages needed OCR.

What happens with it: below `LOW_CONFIDENCE_WARNING` (0.5) the resume gets the
warning `low_confidence`; below `REVIEW_BELOW_CONFIDENCE` (0, off) it would be
held as `needs_review` instead of being indexed.

## Does it follow the real accuracy?

[confidence_results.md](confidence_results.md), from
`python -m scripts.evaluate_confidence`: accuracy is the mean F1 of name,
companies, roles and schools against known entities; pipeline without the
language model.

| Population | CVs | Rank correlation score/accuracy | A bad extraction scores below a good one |
|---|---|---|---|
| synthetic | 120 | 0.65 | 0.99 |
| real (reviewed, 9) | 9 | 0.91 | 1.00 |

By level:

| Level | Synthetic: CVs, mean accuracy, share below 0.5 | Real |
|---|---|---|
| high (0.9 and up) | 106, 0.93, 0% | 3, 0.83, 0% |
| medium | 12, 0.39, 75% | 2, 0.75, 0% |
| low | 2, 0.25, 100% | 4, 0.19, 75% |

Read it as: a `high` CV was right in every case measured, a `low` one almost
always wrong, and `medium` means "read it".

## Limits

- **The 0.9 threshold was chosen after seeing these 129 CVs** (with 0.75 the
  `high` level held 8% bad extractions, all in the 0.8 to 0.9 band). It is
  fitted to this data, not validated on new data. Nine real CVs, labelled by an
  AI assistant and not yet by a person, are far too few to calibrate anything;
  the real-CV correlation has a very wide interval.
- The weights (0.35/0.25/0.20/0.20) were set by hand before measuring and not
  tuned. One check was added after the first measurement: the first version of
  `fields` only looked for presence, and 12 synthetic CVs with complete-looking
  but wrong entries scored 0.87; adding plausibility and date coverage lowered
  them to about 0.84, still not separating them from the good ones except by
  the 0.9 line.
- The score catches extractions that are empty or visibly broken. It cannot
  catch a confidently wrong entry that looks fine (a plausible but wrong
  company). A second opinion (model agreement, grounding in the text) would be
  needed for that and was not built.
- Measured without the language model. With it, more entries come from the
  model, which the score trusts less (0.7 against 1.0), so levels shift down;
  not measured.
- The score says nothing about fairness across languages or backgrounds.
