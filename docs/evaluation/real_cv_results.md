# Results on real CVs

Mode: **full pipeline with the local language model**. 9 reviewed real CVs. Only aggregate numbers are published; the CVs and their labels stay on the machine of their owner.

Intervals are 95% bootstrap intervals over CVs; with this few CVs they are wide, and a difference smaller than the interval is not evidence of anything.

**Core entity F1 (name, companies, roles, schools, degrees, certificates): 0.608 [0.545, 0.678]**

## Fields

| Field | Precision | Recall | F1 | F1 interval | Expected | Found |
|---|---|---|---|---|---|---|
| name | 0.750 | 0.667 | 0.706 | [0.444, 1.000] | 9 | 8 |
| companies | 0.750 | 0.353 | 0.480 | [0.000, 0.727] | 17 | 8 |
| roles | 0.846 | 0.632 | 0.723 | [0.559, 0.894] | 19 | 13 |
| schools | 0.800 | 0.857 | 0.828 | [0.727, 0.952] | 14 | 15 |
| degrees | 0.643 | 0.692 | 0.667 | [0.400, 0.909] | 13 | 14 |
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
| en | 7 | 0.616 |
| other (fewer than 3 each) | 2 | 0.581 |

## By layout

| layout | CVs | Core entity F1 |
|---|---|---|
| multi_column | 4 | 0.590 |
| single | 5 | 0.628 |

## By industry

| industry | CVs | Core entity F1 |
|---|---|---|
| software | 5 | 0.610 |
| other (fewer than 3 each) | 4 | 0.607 |

## Time

Seconds per CV: mean 132.5, median 150.0, max 276.4.

## Sections read by rules or by the model

| Section | Rules | Model |
|---|---|---|
| certifications | 1 | 2 |
| education | 6 | 3 |
| experience | 3 | 5 |
| projects | 3 | 3 |
| summary | 4 | 1 |

