# Section detection

How the CV section detector is measured and what changed. Raw reports:
[before](section_detection_baseline.md) and [after](section_detection.md).

```bash
python -m scripts.evaluate_sections --out docs/evaluation/section_detection.md
```

Round 2 below extends this to other industries, layouts and unfamiliar
headings.

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
- 78 real files (unlabelled, 1 page each) are not part of the score. (The 78 files turned out to be only 9 different CVs, the rest exact copies, so counts out of 78 overstate how varied they are; see [real_cv_README.md](real_cv_README.md).) After the
  change an experience section is found in 63 of them (it was found
  confidently in 1 of 66 before) and the regions needing the LLM fell from 43%
  to 37 in total; 15 of the 78 still show none of experience, education or
  skills.

# Round 2: unfamiliar headings, other industries, other page layouts

The first round fixed headings the lexicon knows. Real CVs also head sections
"Clinical Experience" or "Tools and Platforms", come from fields other than
software, and are laid out in sidebars, banners and timelines. A second corpus
([cv_industries.py](../../app/evaluation/cv_industries.py)) measures that:
6 industries (software, healthcare, finance, marketing, mechanical
engineering, teaching) x 6 layouts (single column, left sidebar, right
sidebar, banner above two columns, timeline with dates in a left column,
long multi-page) x English and Vietnamese x standard or industry-specific
headings = 144 PDFs. The sections appear in varying order, and some documents
carry sections the parser does not extract (languages, interests, references,
publications, memberships): their lines must be dropped, and placing them in
a real section counts as an error.

```bash
python -m scripts.evaluate_sections                  # no LLM, reproducible
python -m scripts.evaluate_sections --heading-llm --out docs/evaluation/section_detection_llm.md
```

## Result (seed 42; line accuracy by heading wording)

| Configuration | Base standard | Base alternate | Industries standard | Industries industry |
|---|---|---|---|---|
| Round 1 (heading lexicon only) | 0.994 | 0.254 | 0.933 | 0.576 |
| + headings found by their look | 0.994 | 0.292 | 0.943 | 0.614 |
| + heading classifier, no LLM ([report](section_detection.md)) | 0.994 | 0.608 | 0.941 | 0.783 |
| + heading classifier + LLM per heading ([report](section_detection_llm.md)) | 0.994 | 0.721 | 0.997 | 0.960 |

Overall line accuracy is 0.860 on the industries corpus without the LLM and
0.978 with it (base corpus: 0.897 and 0.925). The LLM is asked only about the
heading (not the text under it), once per distinct heading: 60 distinct
headings took 261 s (4.4 s each) in the run above, and every later CV with
the same heading is free.

## What changed

- **Two columns were read as one when a heading was wider than its column.**
  The column detector grew a column to the widest block, so a heading
  reaching into the gutter made the narrow blocks of the next column overlap
  it, and text from both columns was interleaved (the contact lines ended up
  in "summary"). Columns are now judged by the typical extent of their blocks
  and by a shared left edge
  ([semantic_region_analyzer.py](../../app/resume_processing/layout/semantic_region_analyzer.py)).
- **Headings are also found by how they look**
  ([heading_style.py](../../app/extraction/section/heading_style.py)). The style
  of the headings the lexicon does know in the same CV (size, weight, case,
  colour, or extra space above) is learned, and any other short line set in
  that style starts a new section, whatever its words. Text under such a
  heading no longer leaks into the section above it. The CV header is never
  treated as a heading, and if more than 10 other short lines share the style
  (for example every employer name is bold) the style is ignored for that CV.
- **Which section an unfamiliar heading starts** is decided, in order, by a
  remembered answer ([heading_cache.py](../../app/extraction/section/heading_cache.py),
  a small JSON file), by the LLM asked about the heading alone, and, when the
  model is unavailable, by comparing the heading's words and the text under it
  with the sections
  ([heading_classifier.py](../../app/extraction/section/heading_classifier.py)).
  Embedding similarity is used only on lines that already look like headings,
  never on arbitrary lines (see "Limits" above for why).
- **Catch-all headings are decided by their content.** In 50 of the 78 real
  CVs the section "Additional Information" holds the skills. Filing it as
  "other" (what the lexicon said, once a filler-word bug was fixed) dropped
  the skills of 50 CVs, so catch-all headings ("Additional Information",
  "Thông tin khác") are no longer in the lexicon; the model may answer
  "mixed" for such a heading, and then the text under it decides.

## Limits

- The corpora are synthetic and the lexicon, the example headings of the
  classifier and the corpus headings were written by the same author. The
  "alternate" and "industry" headings were chosen to differ from the lexicon,
  but they are not an independent sample of how real CVs word their headings.
- Without the LLM the unfamiliar-heading figures are far lower (0.783), because
  the embedding model separates sections poorly from a few words: it is the
  fallback, not the main path. With the LLM, the remaining errors are headings
  the model files differently from the corpus (for example "Key Engagements"
  or a Vietnamese heading ending in "nghề nghiệp").
- A heading is a boundary only if it looks like the known headings of its own
  CV, so a CV whose headings are all unfamiliar and styled differently from
  every known one (no lexicon heading at all) gets no boundary from style.
- Plain-text input (no PDF layout) still uses wording only.
- The cache trusts the model's answer for a heading text; a wrong answer is
  remembered until the cache file is deleted.
- Field-level scoring ([field_eval.py](../../app/evaluation/field_eval.py))
  compares extracted companies, roles, schools, degrees, skills,
  certificates and names with the entities each corpus document was generated
  from. It is tested but not yet run on real extraction output, which needs
  the 7B model for every CV (about 8 minutes each on CPU); that belongs to the
  speed work.
- On the 78 real files (unlabelled, not scored) the new stages ran without (The 78 files turned out to be only 9 different CVs, the rest exact copies, so counts out of 78 overstate how varied they are; see [real_cv_README.md](real_cv_README.md).)
  failures and kept the same sections (skills found in 75 of 78); an average
  of 0.8 headings per CV were found by their look (almost all "Additional
  Information"), and the regions sent to the LLM fallback fell from 41 to 36.
