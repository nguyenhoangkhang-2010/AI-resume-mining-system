# CVs in other languages

Until this change the rule parsers and the heading lexicon knew English and
Vietnamese. A CV in another language went to the language model for every
section, which is slow on CPU, and its headings were guessed by an embedding
model. This change adds vocabulary files for French, Spanish, German,
Portuguese and Russian and fixes the text normalisation that made any
non-Latin script impossible.

## What changed

- **`normalise()` kept only ASCII letters.** Every word of Russian, Greek,
  Arabic or Chinese text became an empty string, so no vocabulary could match
  it (and two different Russian names compared equal). It now keeps letters of
  every script and removes only the accents of Latin letters
  ([heading_lexicon.py](../../app/extraction/section/heading_lexicon.py)).
- **Section headings are data.** The vocabulary files gained a `headings` key
  (headings by section) and a `filler_words` key; the lexicon merges them with
  the built-in English and Vietnamese phrases. Adding a language is adding a
  file ([docs/vocabulary.md](../vocabulary.md)).
- **Five new files:** `fr.json`, `es.json`, `de.json`, `pt.json`, `ru.json` in
  [app/extraction/rules/vocabulary/](../../app/extraction/rules/vocabulary/):
  headings, job titles, employers, schools, degrees, month names, "until now"
  words, range words and places.

## Measured

[multilingual_results.md](multilingual_results.md), produced by
`python -m scripts.evaluate_languages`: 15 invented CVs (three per language,
one column), read by the whole pipeline without a language model, with only the
English and Vietnamese vocabulary (*before*) and with every built-in file
(*after*).

- Lines placed in the right section: 0.22 to 0.28 before, 0.82 to 1.00 after.
- Companies, job titles, schools and degrees: 0.00 before, 0.80 to 1.00 after.
  The name was already found (NER does not depend on the vocabulary).
- Skills F1 is about 0.2 in every language: the skill extractor returns many
  taxonomy skills that a person would not list, as in English.

One Spanish and one Portuguese CV lose their experience section: the third
profile of each language uses headings that no file lists
("Empleos", "Herramientas y métodos", "Trajetória", "Ferramentas e métodos"),
and without the language model the embedding classifier is not sure about
them. The same kind of heading was found by the classifier in French, German
and Russian. With the model (`classify_heading`, cached) such headings are
resolved at the cost of one short call per new heading.

## What this does not show

- The CVs were written by the same hand as the vocabulary files, so the
  vocabulary is partly checked against its own author's wording. The result
  shows that the mechanism works (headings, dates, typed header lines, accents,
  Cyrillic); it is not an accuracy figure for real French, Spanish, German,
  Portuguese or Russian CVs. Real CVs in these languages are the missing piece.
- Single column, three fields, ten to thirty lines each. Layouts, long CVs and
  odd date formats are measured in English only.
- Languages written without spaces between words (Chinese, Japanese, Thai) can
  be recognised by their headings, but the word lists for job titles and
  employers match whole words, so those sections still go to the language model.
- Names are found by NER models (an English one, and `xlm-roberta` for other
  languages); their quality outside English and Vietnamese is not measured here.
- Document titles are deliberately not headings ("Resume", "Résumé",
  "Lebenslauf", "Резюме"), because the lines below them are the name and the
  contact details.
