# Other languages: what the vocabulary files add

Synthetic CVs (invented people, three per language, one column), read by the pipeline without a language model. *Before* has only the English and Vietnamese vocabulary, *after* all built-in files. Line accuracy is the share of lines placed in the right section; the field columns are F1 over the entities of the language's CVs.

| Language | CVs | Lines before | Lines after | name before → after | companies before → after | roles before → after | schools before → after | degrees before → after | skills before → after | certifications before → after |
|---|---|---|---|---|---|---|---|---|---|---|
| fr | 3 | 0.217 | 0.983 | 1.00 → 1.00 | 0.00 → 1.00 | 0.00 → 1.00 | 0.00 → 1.00 | 0.00 → 1.00 | 0.00 → 0.22 | 0.50 → 1.00 |
| es | 3 | 0.233 | 0.817 | 1.00 → 1.00 | 0.00 → 0.80 | 0.00 → 0.80 | 0.00 → 1.00 | 0.00 → 1.00 | 0.00 → 0.24 | 0.40 → 1.00 |
| de | 3 | 0.233 | 1.000 | 1.00 → 1.00 | 0.00 → 1.00 | 0.00 → 1.00 | 0.00 → 1.00 | 0.00 → 1.00 | 0.00 → 0.20 | 0.40 → 1.00 |
| pt | 3 | 0.283 | 0.817 | 1.00 → 1.00 | 0.00 → 0.80 | 0.00 → 0.80 | 0.00 → 1.00 | 0.00 → 1.00 | 0.00 → 0.18 | 0.57 → 1.00 |
| ru | 3 | 0.283 | 1.000 | 1.00 → 1.00 | 0.00 → 0.80 | 0.00 → 0.80 | 0.00 → 1.00 | 0.00 → 0.80 | 0.00 → 0.24 | 0.57 → 1.00 |
