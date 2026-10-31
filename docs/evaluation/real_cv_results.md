# Results on real CVs

Mode: **full pipeline with the local language model**. 9 reviewed real CVs. Only aggregate numbers are published; the CVs and their labels stay on the machine of their owner.

Intervals are 95% bootstrap intervals over CVs; with this few CVs they are wide, and a difference smaller than the interval is not evidence of anything.

**Core entity F1 (name, companies, roles, schools, degrees, certificates): 0.620 [0.534, 0.752]**

## Fields

| Field | Precision | Recall | F1 | F1 interval | Expected | Found |
|---|---|---|---|---|---|---|
| name | 0.750 | 0.667 | 0.706 | [0.444, 1.000] | 9 | 8 |
| companies | 0.889 | 0.471 | 0.615 | [0.333, 0.889] | 17 | 9 |
| roles | 0.857 | 0.684 | 0.761 | [0.571, 0.957] | 19 | 14 |
| schools | 0.857 | 0.857 | 0.857 | [0.757, 0.960] | 14 | 14 |
| degrees | 0.500 | 0.615 | 0.552 | [0.345, 0.766] | 13 | 18 |
| skills | 0.105 | 0.328 | 0.159 | [0.093, 0.237] | 137 | 429 |
| certifications | 0.182 | 0.167 | 0.174 | [0.000, 0.381] | 12 | 11 |

`skills` precision is low by construction: the extractor returns taxonomy skills that a person would not list; read its recall.

## Sections found

| Section | Precision | Recall | CVs that have it |
|---|---|---|---|
| summary | 1.000 | 1.000 | 5 |
| experience | 0.875 | 1.000 | 7 |
| education | 1.000 | 1.000 | 9 |
| skills | 1.000 | 1.000 | 8 |
| projects | 0.833 | 1.000 | 5 |
| certifications | 1.000 | 1.000 | 3 |

## By language

| language | CVs | Core entity F1 |
|---|---|---|
| en | 7 | 0.641 |
| other (fewer than 3 each) | 2 | 0.533 |

## By layout

| layout | CVs | Core entity F1 |
|---|---|---|
| multi_column | 4 | 0.550 |
| single | 5 | 0.688 |

## By industry

| industry | CVs | Core entity F1 |
|---|---|---|
| software | 5 | 0.681 |
| other (fewer than 3 each) | 4 | 0.572 |

## Time

Seconds per CV: mean 161.6, median 177.7, max 383.8.

## Sections read by rules or by the model

| Section | Rules | Model |
|---|---|---|
| certifications | 1 | 2 |
| education | 3 | 6 |
| experience | 4 | 4 |
| projects | 2 | 4 |
| summary | 4 | 1 |

