# Extraction speed

Reading one CV with the local 7B model on a CPU took about **400 seconds** (407 s on the 4 CVs below, 430 s in an earlier run). This
page explains where that time went, what was changed, and what it did to
speed and to the fields found. Raw reports:
[before](extraction_speed_baseline.md) (the same code with the new features switched off) and
[after](extraction_speed.md).

```bash
python -m scripts.benchmark_extraction --documents 4 --out docs/evaluation/extraction_speed.md
```

The script runs the real pipeline (PDF, layout, sections, all extractors, the
GGUF model) on 4 synthetic English CVs from different industries and layouts
and records, per extractor, the time and the model calls. It scores the
companies, roles, schools, degrees, certificates and names it found against the
entities the CV was generated from. It needs the model, so it is a script and
not a test.

## Where the time went (before)

| Stage | Seconds per CV |
|---|---|
| sections (layout, headings, model calls for unclear regions) | 32 |
| summary | 34 |
| education | 51 |
| experience | 101 |
| projects | 129 |
| certifications | 60 |
| everything else | 1 |

Almost all of it was the model. A CPU reads about twenty prompt tokens a second
and writes a few, and each extractor sent a long instruction block (several
hundred tokens, identical for every CV) followed by the CV section, then asked
for a JSON answer of up to 768 tokens.

## What changed

1. **Regular sections are read with rules, the model is the fallback**
   ([app/extraction/rules](../../app/extraction/rules)). Experience (date ranges
   mark the jobs; the header lines beside each date hold role and company),
   education (school lines with the degree, years and GPA around them),
   summary (the section already is the summary), certifications (one per line)
   and projects (a title followed by bullets or a paragraph) are parsed
   directly. Each parser answers only when *every* line is accounted for; if a
   header cannot be split into role and company, there is text before the first
   job, a short line may be the wrapped end of the previous one, and so on, it
   returns "unclear" and the section goes to the model as before. So an unusual
   CV costs what it cost before, not more. Switch: `EXTRACTION_RULES_FIRST`.
2. **The instructions of each prompt are read once.** The model's state after
   the fixed instruction block is kept in memory per prompt and restored for the
   next CV ([prefix_cache.py](../../app/extraction/llm/prefix_cache.py)), so only
   the CV text has to be read. The answer is unchanged. Memory:
   `LLM_PREFIX_CACHE_MB` (default 1024, 0 turns it off).
3. **Identical prompts are answered from memory** (`LLM_RESULT_CACHE_SIZE`,
   nothing is written to disk, so deleting a candidate leaves no copy).
4. **Model calls are serialised.** The local model is not thread-safe, and CVs
   are processed in worker threads; two at once could corrupt each other.

## Result (4 CVs, same machine)

Seconds per CV and fields found, each row switching one change on. The same
machine, the same 4 CVs, the model's answers are unchanged by the instruction
cache (the field columns of rows 1 and 2 are identical).

| Configuration | Seconds per CV | Model calls per CV | Companies found | Roles found | Degrees found |
|---|---|---|---|---|---|
| Before (rules off, instruction cache off) | 407 | 8.2 | 1 of 9 | 1 of 7 | 2 of 4 |
| Instruction cache only | 219 | 8.2 | 1 of 9 | 1 of 7 | 2 of 4 |
| Rules only | 65 | 3.8 | 9 of 9 | 7 of 7 | 4 of 4 |
| **Both (default)** | **42** | **3.8** | **9 of 9** | **7 of 7** | **4 of 4** |

Per CV (both on): 28, 83, 4 and 51 s. Where the model is still used: the
section step (about 17 s per CV: unfamiliar headings and regions without a
clear heading) and the certification lists that may contain wrapped lines. In
the instruction-cache-only row the first CV took 383 s because it read each
instruction block once; the next three took 110 to 201 s.

Per stage, before and after (seconds per CV):

| Stage | Before | After |
|---|---|---|
| sections | 32 | 17 |
| summary | 34 | 0 |
| education | 51 | 0 |
| experience | 101 | 0 |
| projects | 129 | 0 |
| certifications | 60 | 22 |
| skills and personal info | 1 | 2 |

## Limits (read before trusting the numbers)

- The CVs are synthetic and the title/employer vocabulary of the rules was
  written by the same author as the corpus, so the 100% on companies, roles and
  schools is optimistic. The comparison that matters is the one between rows:
  the same CVs, with and without each change.
- **On real CVs the rules answer less often.** (The 78 files turned out to be only 9 different CVs, the rest exact copies, so counts out of 78 overstate how varied they are; see [real_cv_README.md](real_cv_README.md).) On 78 real CVs (unlabelled, not
  scored) they read the education section in 72 of 78 cases and the summary in
  55 of 56, but the experience section in only 7 of 64: 50 of those CVs share
  one header ("ABBREVIATION - Company name", no job title) that the rules
  deliberately refuse to guess. Those go to the model, with the same cost as
  before apart from the instruction cache. The speed-up on a real batch is
  therefore smaller than the table. To time your own CVs (no scores; file
  names are not printed or written):

  ```bash
  python -m scripts.benchmark_extraction --folder data/uploads --documents 5 --out my_speed.md
  ```
- The model path still has its old weak spots (companies often null, bullets
  dropped, see the "before" report); the rules path is better there, because
  it does not ask the model to re-type text it can copy.
- "skills" is scored against the corpus skill list but the extractor draws on a
  13,949-skill taxonomy, so its precision here (0.15) mostly measures the
  taxonomy size; it did not change.
- The first CV after a start still reads each instruction block once; and a CV
  whose experience needs the model still takes minutes.
- What remains of the time is the section step (about 17 s): model calls to
  classify regions and unfamiliar headings. Headings are remembered across CVs
  (see [section_detection_README.md](section_detection_README.md)); regions
  without a clear heading still go to the model.
