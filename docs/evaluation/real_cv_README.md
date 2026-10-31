# Evaluation on real CVs

Every other evaluation in this repository uses synthetic CVs, so none of it
shows how the system does on real ones. This page describes how to build a
small labelled set of real CVs and score the pipeline on it, without putting
personal data in the repository.

**Privacy.** Real CVs are personal data. The PDFs and the label files stay in
`data/real_cv_eval/` and `data/uploads/`, which are git-ignored. The scripts
print no CV text and no file names, labels use anonymous ids (`cv-001`), and
the report that may be published contains only aggregate numbers; a group of
fewer than 3 CVs is never reported on its own.

## Workflow

```bash
# 1. choose a varied subset (near-identical templates are capped)
python -m scripts.real_cv_prepare pick --folder data/uploads --count 40

# 2. write draft labels from what the system extracts (fast: no LLM)
python -m scripts.real_cv_prepare draft --folder data/uploads

# 3. for each CV: open it, correct the label, mark it reviewed
python -m scripts.real_cv_prepare open cv-001
python -m scripts.real_cv_prepare mark cv-001
python -m scripts.real_cv_prepare check         # what is left, any mistakes

# 4. score (aggregate report) and list the weakest CVs by id
python -m scripts.evaluate_real_cvs --mode rules --out docs/evaluation/real_cv_results.md
python -m scripts.evaluate_real_cvs --mode full  --out docs/evaluation/real_cv_results_full.md
```

`--mode rules` switches the language model off, so it shows what the rules, NER
and embedding models do alone and runs in seconds. `--mode full` runs the
pipeline exactly as the API does (minutes per CV that the rules cannot read).
`draft --llm` drafts with the model instead.

Only labels with `"status": "reviewed"` are scored. `mark` refuses a label
that fails validation (no PDF name, unknown field names, no entities at all).

## The label file

```json
{
  "id": "cv-001",
  "file": "the-pdf-name.pdf",
  "status": "reviewed",
  "tags": {"language": "vi", "industry": "marketing", "layout": "single", "pages": "1"},
  "sections_present": ["summary", "experience", "education", "skills"],
  "entities": {
    "name": ["..."], "companies": ["..."], "roles": ["..."], "schools": ["..."],
    "degrees": ["..."], "skills": ["..."], "certifications": ["..."]
  },
  "notes": ""
}
```

Rules for labelling, so that two people would label the same way:

- **Entities are what the CV states**, written as in the CV; case, accents and
  punctuation do not matter and a value contained in a longer extracted text
  counts as found.
- `companies` and `roles` list each employer and each job title once (not
  schools, not projects). `schools` are institutions; `degrees` the degree or
  programme line ("BSc in Nursing"). `certifications` are certificates and
  licences, not awards.
- `skills`: skills the CV lists or clearly uses, not what you infer. The score
  for this field is dominated by the taxonomy returning skills nobody listed,
  so read its recall, not its precision.
- `sections_present`: sections the CV really has, whatever its heading
  (summary, experience, education, skills, projects, certifications).
- `tags`: `industry` is free text you choose (keep the spelling consistent so
  CVs group together); `language` is the main language of the CV; `layout`
  is `single` or `multi_column`.
- Leave a list empty if the CV has none. Do not label a CV you could not
  verify against the PDF.

## What is reported

For the reviewed CVs: precision, recall and F1 per field with a 95% bootstrap
interval over CVs; one headline "core entity F1" (name, companies, roles,
schools, degrees, certificates together); whether each section was found;
results by language, layout and industry; time per CV; and how many sections
the rules answered versus the model.

## Limits of this evaluation

- **Anchoring.** Draft labels come from the system's own output, and people
  tend to accept a draft. This overstates quality somewhat. To reduce it, add
  what the draft is missing before judging what it contains, and label a few
  CVs from scratch (clear the entities in the file) to compare.
- **Small samples.** Thirty to forty CVs give wide intervals; a difference
  smaller than the interval is not a difference.
- **Representativeness.** The set is only as varied as the CVs collected. The
  score says how the system does on *these kinds* of CVs.

## Where the data stands

The 78 PDFs currently in `data/uploads` are not varied enough to support a
claim about "any language, industry or format": `pick` finds that 50 of them
share almost the same text (one template), another 14 form a second group, and
after removing near-duplicates 15 remain. All 78 have one page, 73 are English
and 69 have one column. A set that tests the goals of this project needs, at
least, CVs that are multi-page, in other languages, from other industries,
with two-column and designed layouts, and some scanned ones.
