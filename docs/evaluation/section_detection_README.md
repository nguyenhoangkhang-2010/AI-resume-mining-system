# Section detection

How the CV section detector is measured and what changed. Raw reports:
[before](section_detection_baseline.md) and [after](section_detection.md).

```bash
python -m scripts.evaluate_sections --out docs/evaluation/section_detection.md
```

The script builds PDFs with known sections (6 heading styles x single column,
two columns and several pages x English and Vietnamese, plus a set with
alternate heading wording), runs the real pipeline up to section detection
and scores every body line. The LLM fallback is replaced by a stub, so the
numbers show what the deterministic stages achieve on their own.

## Result (96 synthetic PDFs, 2,735 body lines, same corpus before and after)

| | Before | After |
|---|---|---|
| Line accuracy, standard heading wording | 0.113 | 0.994 |
| Line accuracy, alternate heading wording | 0.126 | 0.254 |
| Regions that would call the LLM fallback | 205 | 54 |

Before the change, accuracy was low for every heading style, layout and
language because the embedding classifier is rarely confident and the stubbed
fallback dropped those regions. After it, accuracy no longer depends on the
heading style (uppercase, bold at body size, tight spacing), the layout or the
language.

## What changed

- Headings are recognised by wording, in English and Vietnamese, with or
  without diacritics ([heading_lexicon.py](../../app/extraction/section/heading_lexicon.py)),
  and split a region wherever they appear, so layout analysis no longer has
  to find them from font size.
- The CV header (name and contact lines) is recognised from the contact
  details; the text after it is classified on its own.
- A region without a heading on a later page continues the previous section
  when it is in the same column.
- PDF text is normalised (decomposed accents, ligatures, non-breaking spaces,
  soft hyphens) before analysis.

## Limits (read before trusting the numbers)

- The corpus is synthetic and its standard headings are the ones the lexicon
  was written around, so 0.994 is optimistic.
- **Headings with unfamiliar wording are still a weak spot** (0.254 without
  the LLM). In production these regions go to the embedding classifier and
  then the LLM fallback, whose accuracy was not measured here because it
  needs the local 7B model.
- Matching unfamiliar headings by embedding similarity was tried and
  rejected: it mislabelled ordinary lines (for example the major name
  "Information Technology" scored as a skills heading with similarity 0.82).
- 78 real CVs (unlabelled, 1 page each) are not part of the score. After the
  change an experience section is found in 63 of them (it was found
  confidently in 1 of 66 before) and the regions needing the LLM fell from 43%
  to 37 in total; 15 of the 78 still show none of experience, education or
  skills.
