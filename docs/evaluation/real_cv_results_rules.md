# Results on real CVs

Mode: **rules, NER and embeddings only (language model off)**. 9 reviewed real CVs. Only aggregate numbers are published; the CVs and their labels stay on the machine of their owner.

Intervals are 95% bootstrap intervals over CVs; with this few CVs they are wide, and a difference smaller than the interval is not evidence of anything.

**Core entity F1 (name, companies, roles, schools, degrees, certificates): 0.482 [0.186, 0.759]**

## Fields

| Field | Precision | Recall | F1 | F1 interval | Expected | Found |
|---|---|---|---|---|---|---|
| name | 0.833 | 0.556 | 0.667 | [0.364, 0.941] | 9 | 6 |
| companies | 1.000 | 0.353 | 0.522 | [0.125, 1.000] | 17 | 6 |
| roles | 1.000 | 0.421 | 0.593 | [0.129, 1.000] | 19 | 8 |
| schools | 1.000 | 0.286 | 0.444 | [0.000, 0.762] | 14 | 4 |
| degrees | 1.000 | 0.308 | 0.471 | [0.000, 0.762] | 13 | 4 |
| skills | 0.107 | 0.328 | 0.162 | [0.095, 0.241] | 137 | 419 |
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
| en | 7 | 0.484 |
| other (fewer than 3 each) | 2 | 0.471 |

## By layout

| layout | CVs | Core entity F1 |
|---|---|---|
| multi_column | 4 | 0.286 |
| single | 5 | 0.635 |

## By industry

| industry | CVs | Core entity F1 |
|---|---|---|
| software | 5 | 0.600 |
| other (fewer than 3 each) | 4 | 0.387 |

## Time

Seconds per CV: mean 3.3, median 3.4, max 6.1.

## Sections read by rules or by the model

| Section | Rules | Model |
|---|---|---|
| certifications | 0 | 2 |
| education | 3 | 6 |
| experience | 4 | 4 |
| projects | 2 | 4 |
| summary | 3 | 1 |

