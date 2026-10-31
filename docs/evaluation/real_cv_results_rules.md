# Results on real CVs

Mode: **rules, NER and embeddings only (language model off)**. 9 reviewed real CVs. Only aggregate numbers are published; the CVs and their labels stay on the machine of their owner.

Intervals are 95% bootstrap intervals over CVs; with this few CVs they are wide, and a difference smaller than the interval is not evidence of anything.

**Core entity F1 (name, companies, roles, schools, degrees, certificates): 0.492 [0.316, 0.677]**

## Fields

| Field | Precision | Recall | F1 | F1 interval | Expected | Found |
|---|---|---|---|---|---|---|
| name | 0.833 | 0.556 | 0.667 | [0.364, 0.941] | 9 | 6 |
| companies | 0.667 | 0.118 | 0.200 | [0.000, 0.600] | 17 | 3 |
| roles | 1.000 | 0.263 | 0.417 | [0.000, 0.818] | 19 | 5 |
| schools | 0.750 | 0.643 | 0.692 | [0.462, 0.857] | 14 | 12 |
| degrees | 1.000 | 0.615 | 0.762 | [0.471, 0.947] | 13 | 8 |
| skills | 0.108 | 0.328 | 0.163 | [0.096, 0.244] | 137 | 415 |
| certifications | 0.000 | 0.000 | 0.000 | [0.000, 0.000] | 12 | 0 |

`skills` precision is low by construction: the extractor returns taxonomy skills that a person would not list; read its recall.

## Sections found

| Section | Precision | Recall | CVs that have it |
|---|---|---|---|
| summary | 1.000 | 0.800 | 5 |
| experience | 0.875 | 1.000 | 7 |
| education | 1.000 | 1.000 | 9 |
| skills | 1.000 | 1.000 | 8 |
| projects | 0.833 | 1.000 | 5 |
| certifications | 1.000 | 0.667 | 3 |

## By language

| language | CVs | Core entity F1 |
|---|---|---|
| en | 7 | 0.469 |
| other (fewer than 3 each) | 2 | 0.600 |

## By layout

| layout | CVs | Core entity F1 |
|---|---|---|
| multi_column | 4 | 0.400 |
| single | 5 | 0.571 |

## By industry

| industry | CVs | Core entity F1 |
|---|---|---|
| software | 5 | 0.577 |
| other (fewer than 3 each) | 4 | 0.424 |

## Time

Seconds per CV: mean 7.8, median 8.3, max 14.1.

## Sections read by rules or by the model

| Section | Rules | Model |
|---|---|---|
| certifications | 0 | 2 |
| education | 6 | 3 |
| experience | 3 | 5 |
| projects | 3 | 3 |
| summary | 3 | 1 |

