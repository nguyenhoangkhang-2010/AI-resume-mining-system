# Vocabulary files

The rule parsers (`app/extraction/rules/`) read experience, education,
certificates, projects and summaries without the language model when the layout
is regular. To do that they need to know some words: which words make a line a
job title, which an employer, which a school or a degree, how months are spelled,
which words mean "until now", which names are places. Those words are data, in
JSON files, not code.

Built in: [en.json](../app/extraction/rules/vocabulary/en.json) and
[vi.json](../app/extraction/rules/vocabulary/vi.json). Every `*.json` file in
that folder is loaded and merged.

## Adding a language, or a field's own words

Write a file in the same format and point `VOCABULARY_DIR` at its folder (in
Docker, mount the folder and set the variable). Files there are merged with the
built-in ones; nothing in the code changes. Example for French:

```json
{
  "language": "fr",
  "roles": {"words": ["ingénieur", "développeur"], "phrases": ["chef de projet"]},
  "companies": {"words": ["sarl"], "phrases": ["société", "groupe"]},
  "institutions": {"words": ["université", "école"]},
  "degrees": {"words": ["licence", "master"]},
  "months": ["janvier", "février", "mars"],
  "present": ["aujourd'hui", "à ce jour"],
  "places": {"words": ["france"], "phrases": ["paris"]}
}
```

| Key | Meaning |
|---|---|
| `roles`, `companies`, `institutions`, `degrees`, `places` | `words` match one whole word, `phrases` several words in a row |
| `company_suffixes` | words such as `ltd` whose full stop belongs to the name ("Acme Ltd.") |
| `months` | month names, full and abbreviated (used in "Mar 2021", "Tháng 3/2021") |
| `present` | words for "until now" ("present", "nay", "aujourd'hui") |
| `range_words` | words that join the two ends of a range besides dashes ("to", "đến") |

Entries may be written naturally, with capitals and accents; they are
normalised when loaded, the same way the text is, so `Kỹ sư`, `KY SU` and
`ky su` are one entry. A file that cannot be read, has an unknown key or a
value of the wrong type stops the load with an error naming the file.

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
