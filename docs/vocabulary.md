# Vocabulary files

The rule parsers (`app/extraction/rules/`) read experience, education,
certificates, projects and summaries without the language model when the layout
is regular. To do that they need to know some words: which words make a line a
job title, which an employer, which a school or a degree, how months are spelled,
which words mean "until now", which names are places. Those words are data, in
JSON files, not code.

Built in, one file per language in
[app/extraction/rules/vocabulary/](../app/extraction/rules/vocabulary/): English,
Vietnamese, French, Spanish, German, Portuguese and Russian. Every `*.json` file
in that folder is loaded and merged. The French, Spanish, German, Portuguese and
Russian files were written for this project and checked on a handful of invented
CVs only ([multilingual_README.md](evaluation/multilingual_README.md)); treat them as a start
that real CVs will extend.

## Adding a language, or a field's own words

Write a file in the same format and point `VOCABULARY_DIR` at its folder (in
Docker, mount the folder and set the variable). Files there are merged with the
built-in ones; nothing in the code changes. Example for Italian:

```json
{
  "language": "it",
  "roles": {"words": ["ingegnere", "sviluppatore"], "phrases": ["capo progetto"]},
  "companies": {"words": ["srl", "spa"], "phrases": ["società", "gruppo"]},
  "institutions": {"words": ["università", "scuola"]},
  "degrees": {"words": ["laurea", "master"]},
  "months": ["gennaio", "febbraio", "marzo"],
  "present": ["oggi", "ad oggi"],
  "places": {"words": ["italia"], "phrases": ["roma"]},
  "headings": {"experience": ["esperienza lavorativa"], "education": ["istruzione"]},
  "filler_words": ["e"]
}
```

| Key | Meaning |
|---|---|
| `roles`, `companies`, `institutions`, `degrees`, `places` | `words` match one whole word, `phrases` several words in a row |
| `company_suffixes` | words such as `ltd` whose full stop belongs to the name ("Acme Ltd.") |
| `months` | month names, full and abbreviated (used in "Mar 2021", "Tháng 3/2021") |
| `present` | words for "until now" ("present", "nay", "aujourd'hui") |
| `range_words` | words that join the two ends of a range besides dashes ("to", "đến") |
| `headings` | section headings of the language, by section (`personal_info`, `summary`, `experience`, `education`, `skills`, `projects`, `certifications`, `other`) |
| `filler_words` | small words that may surround a heading ("and", "de", "und") |

Entries may be written naturally, with capitals and accents; they are
normalised when loaded, the same way the text is, so `Kỹ sư`, `KY SU` and
`ky su` are one entry. A file that cannot be read, has an unknown key or a
value of the wrong type stops the load with an error naming the file.

Letters of other scripts (Cyrillic, Greek, Arabic, Devanagari ...) are kept when
text is normalised; only the accents of Latin letters are removed. Languages
written without spaces between words (Chinese, Japanese, Thai) work for
headings, which are one token, but not for the word lists of job titles and
employers, which are matched word by word.

A heading that is also the title of the document is left out on purpose
("Resume", "Résumé", "Lebenslauf", "Резюме"): the name and contact lines
below it would otherwise be read as a summary.

## What the vocabulary is for, and what it is not

It is a hint, not a list of valid titles. A header line is typed as a title, an
employer or a place from these words; if the lines of a job cannot be typed
(two titles, two unknown lines, a title word on both sides) the parser gives up
and the section goes to the language model. So a missing word costs speed, not
correctness, and a word that is wrong for your field (for example "head", which
is a title in "Head of Sales" and not in "Head Office") can be fixed in the file.

Some choices are visible in the files: "technology" is not an employer word
(it is in "Information Technology Support Specialist"); "head" is a title only
as the phrase "head of"; "trường" (school) is an institution word but not an
employer word, because "trưởng" (head of) is a title.

How well the rules do on real CVs, with and without the vocabulary changes, is
in [evaluation/real_cv_README.md](evaluation/real_cv_README.md).
