# Offline evaluation on the synthetic dataset

Generated 2026-10-28 by `scripts/run_evaluation.py` (dataset seed 42, embedding: real).

- Jobs: 30
- Candidates: 300

## Limitations

- The data is synthetic. Labels come from latent attributes (role family, years of experience), and skill lists are generated with noise (missing skills, off-role skills, alias spellings, keyword stuffers). The numbers measure behaviour under that noise model, not real-world hiring accuracy.
- The noise parameters were raised once after a first version made every ranker score ~1.0 on family-only labels; they were not tuned towards any ranker.
- Only 30 jobs are used, so confidence intervals are wide; read differences together with the paired intervals.
- The ranker named `hybrid` is the production scoring path (skill coverage + skills-only embedding + experience) without its minimum-score filter.

## Ranking

### Labels: `seniority_aware`

Labels combine role family and seniority (0-3): same family and enough experience = 3, one year short = 2, otherwise 1; adjacent family with enough experience = 1.

Mean over jobs with 95% bootstrap confidence interval.

| Ranker | ndcg@10 | ndcg@50 | mrr | map | recall@50 | precision@10 |
|---|---|---|---|---|---|---|
| bm25 | 0.784 [0.718, 0.849] | 0.672 [0.635, 0.708] | 0.908 [0.825, 0.975] | 0.606 [0.558, 0.655] | 0.636 [0.594, 0.674] | 0.813 [0.757, 0.870] |
| tfidf | 0.786 [0.719, 0.851] | 0.646 [0.611, 0.678] | 0.917 [0.850, 0.983] | 0.573 [0.531, 0.615] | 0.596 [0.554, 0.635] | 0.810 [0.743, 0.873] |
| skill_overlap | 0.675 [0.600, 0.750] | 0.630 [0.585, 0.675] | 0.841 [0.728, 0.936] | 0.545 [0.486, 0.604] | 0.613 [0.563, 0.659] | 0.687 [0.610, 0.763] |
| semantic_skills | 0.649 [0.560, 0.737] | 0.632 [0.574, 0.692] | 0.876 [0.776, 0.958] | 0.546 [0.472, 0.621] | 0.619 [0.559, 0.680] | 0.650 [0.557, 0.743] |
| semantic_fulltext | 0.777 [0.717, 0.833] | 0.645 [0.601, 0.686] | 0.940 [0.863, 1.000] | 0.572 [0.523, 0.622] | 0.598 [0.547, 0.648] | 0.813 [0.747, 0.877] |
| hybrid_no_experience | 0.680 [0.597, 0.761] | 0.660 [0.608, 0.709] | 0.836 [0.733, 0.930] | 0.579 [0.513, 0.646] | 0.658 [0.611, 0.704] | 0.710 [0.623, 0.793] |
| hybrid | 0.855 [0.796, 0.910] | 0.741 [0.701, 0.780] | 0.950 [0.900, 1.000] | 0.654 [0.603, 0.703] | 0.685 [0.641, 0.730] | 0.850 [0.790, 0.907] |

Paired difference in nDCG@10 (hybrid minus other ranker, same jobs):

| Compared with | Δ ndcg@10 (95% CI) |
|---|---|
| bm25 | +0.072 [+0.006, +0.134] (significant) |
| tfidf | +0.069 [-0.004, +0.137] (not significant) |
| skill_overlap | +0.180 [+0.118, +0.244] (significant) |
| semantic_skills | +0.206 [+0.143, +0.269] (significant) |
| semantic_fulltext | +0.078 [+0.020, +0.134] (significant) |
| hybrid_no_experience | +0.175 [+0.126, +0.227] (significant) |

### Labels: `family_only`

Labels depend only on role family (0-2): same family = 2, adjacent family = 1. Seniority is ignored.

Mean over jobs with 95% bootstrap confidence interval.

| Ranker | ndcg@10 | ndcg@50 | mrr | map | recall@50 | precision@10 |
|---|---|---|---|---|---|---|
| bm25 | 0.952 [0.916, 0.980] | 0.722 [0.690, 0.752] | 0.983 [0.950, 1.000] | 0.689 [0.643, 0.731] | 0.609 [0.567, 0.647] | 0.933 [0.890, 0.970] |
| tfidf | 0.968 [0.931, 0.993] | 0.696 [0.665, 0.725] | 1.000 [1.000, 1.000] | 0.657 [0.613, 0.695] | 0.570 [0.531, 0.606] | 0.953 [0.900, 0.990] |
| skill_overlap | 0.883 [0.850, 0.915] | 0.713 [0.680, 0.745] | 0.983 [0.950, 1.000] | 0.658 [0.609, 0.705] | 0.608 [0.565, 0.650] | 0.843 [0.797, 0.887] |
| semantic_skills | 0.834 [0.777, 0.891] | 0.687 [0.642, 0.732] | 0.967 [0.917, 1.000] | 0.629 [0.564, 0.696] | 0.593 [0.540, 0.644] | 0.783 [0.710, 0.857] |
| semantic_fulltext | 0.923 [0.865, 0.969] | 0.694 [0.657, 0.729] | 0.957 [0.887, 1.000] | 0.647 [0.598, 0.692] | 0.576 [0.531, 0.619] | 0.907 [0.847, 0.957] |
| hybrid_no_experience | 0.888 [0.838, 0.934] | 0.736 [0.700, 0.772] | 0.967 [0.917, 1.000] | 0.688 [0.635, 0.741] | 0.642 [0.599, 0.686] | 0.867 [0.810, 0.917] |
| hybrid | 0.896 [0.846, 0.940] | 0.705 [0.672, 0.739] | 0.950 [0.900, 1.000] | 0.647 [0.600, 0.694] | 0.600 [0.561, 0.640] | 0.877 [0.823, 0.927] |

Paired difference in nDCG@10 (hybrid minus other ranker, same jobs):

| Compared with | Δ ndcg@10 (95% CI) |
|---|---|
| bm25 | -0.057 [-0.109, -0.010] (significant) |
| tfidf | -0.072 [-0.128, -0.022] (significant) |
| skill_overlap | +0.012 [-0.030, +0.054] (not significant) |
| semantic_skills | +0.062 [+0.020, +0.103] (significant) |
| semantic_fulltext | -0.028 [-0.082, +0.028] (not significant) |
| hybrid_no_experience | +0.007 [-0.018, +0.035] (not significant) |

## Skill extraction

Rule/semantic `SkillExtractor` on synthetic resume text. Only skills in the evaluated vocabulary are scored.

| Metric | Value |
|---|---|
| Documents | 100 |
| Precision | 0.965 |
| Recall | 0.466 |
| F1 | 0.628 |
| Extra skills outside vocabulary / document | 3.5 |

Lowest per-skill recall (fraction of documents where the skill was found):

| Skill | Recall |
|---|---|
| airflow | 0.00 |
| android | 0.00 |
| azure | 0.00 |
| bigquery | 0.00 |
| ci/cd | 0.00 |
| dbt | 0.00 |
| django | 0.00 |
| figma | 0.00 |
| firebase | 0.00 |
| flutter | 0.00 |
| gcp | 0.00 |
| grafana | 0.00 |
| graphql | 0.00 |
| helm | 0.00 |
| html | 0.00 |

