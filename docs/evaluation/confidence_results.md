# Does the confidence score follow the accuracy?

Mode: `rules` (no language model; rules, NER and embeddings only). Accuracy is the mean F1 over name, companies, roles, schools.

### Synthetic CVs

- CVs: 120 (11 with accuracy below 0.5)
- Mean accuracy: 0.860
- Rank correlation between score and accuracy (Spearman): 0.65
- Chance a bad extraction scores below a good one: 0.99

| Level | CVs | Mean accuracy | Share with accuracy below 0.5 |
|---|---|---|---|
| high | 106 | 0.925 | 0.00 |
| medium | 12 | 0.392 | 0.75 |
| low | 2 | 0.250 | 1.00 |

| Score | CVs | Mean accuracy | Share with accuracy below 0.5 |
|---|---|---|---|
| 0.9 to 1.0 | 106 | 0.925 | 0.00 |
| 0.8 to 0.9 | 12 | 0.392 | 0.75 |
| 0.7 to 0.8 | 0 | - | - |
| 0.5 to 0.7 | 0 | - | - |
| 0.0 to 0.5 | 2 | 0.250 | 1.00 |

### Real CVs (reviewed)

- CVs: 9 (3 with accuracy below 0.5)
- Mean accuracy: 0.528
- Rank correlation between score and accuracy (Spearman): 0.91
- Chance a bad extraction scores below a good one: 1.00

| Level | CVs | Mean accuracy | Share with accuracy below 0.5 |
|---|---|---|---|
| high | 3 | 0.833 | 0.00 |
| medium | 2 | 0.750 | 0.00 |
| low | 4 | 0.188 | 0.75 |

| Score | CVs | Mean accuracy | Share with accuracy below 0.5 |
|---|---|---|---|
| 0.9 to 1.0 | 3 | 0.833 | 0.00 |
| 0.8 to 0.9 | 2 | 0.750 | 0.00 |
| 0.7 to 0.8 | 0 | - | - |
| 0.5 to 0.7 | 0 | - | - |
| 0.0 to 0.5 | 4 | 0.188 | 0.75 |
