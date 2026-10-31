# Offline evaluation on the synthetic dataset

Generated 2026-10-28 by `scripts/run_evaluation.py` (dataset seed 42, embedding: real).

- Jobs: 30
- Candidates: 300

## Limitations

- The data is synthetic. Labels come from latent attributes (role family, years of experience), and skill lists are generated with noise (missing skills, off-role skills, alias spellings, keyword stuffers). The numbers measure behaviour under that noise model, not real-world hiring accuracy.
- The noise parameters were raised once after a first version made every ranker score ~1.0 on family-only labels; they were not tuned towards any ranker.
- Only 30 jobs are used, so confidence intervals are wide; read differences together with the paired intervals.
- The ranker named `hybrid` is the production scoring path (skill coverage + profile-text embedding + experience) without its minimum-score filter. `hybrid_skills_embedding` is the same path with the earlier skills-only embedding, for comparison.

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
| semantic_profile_concat | 0.747 [0.677, 0.812] | 0.607 [0.564, 0.645] | 0.911 [0.833, 0.983] | 0.525 [0.483, 0.567] | 0.556 [0.509, 0.603] | 0.770 [0.703, 0.830] |
| semantic_profile_pooled | 0.740 [0.659, 0.813] | 0.632 [0.578, 0.680] | 0.903 [0.819, 0.983] | 0.556 [0.496, 0.614] | 0.590 [0.537, 0.639] | 0.753 [0.667, 0.833] |
| hybrid_skills_embedding | 0.855 [0.796, 0.910] | 0.741 [0.701, 0.780] | 0.950 [0.900, 1.000] | 0.654 [0.603, 0.703] | 0.685 [0.641, 0.730] | 0.850 [0.790, 0.907] |
| hybrid_no_experience | 0.724 [0.655, 0.794] | 0.689 [0.645, 0.731] | 0.898 [0.808, 0.975] | 0.605 [0.546, 0.662] | 0.678 [0.632, 0.724] | 0.737 [0.663, 0.810] |
| hybrid | 0.894 [0.851, 0.934] | 0.778 [0.746, 0.806] | 1.000 [1.000, 1.000] | 0.688 [0.643, 0.727] | 0.723 [0.678, 0.764] | 0.877 [0.823, 0.927] |

Paired difference in nDCG@10 (hybrid minus other ranker, same jobs):

| Compared with | Δ ndcg@10 (95% CI) |
|---|---|
| bm25 | +0.110 [+0.057, +0.164] (significant) |
| tfidf | +0.108 [+0.051, +0.166] (significant) |
| skill_overlap | +0.219 [+0.158, +0.284] (significant) |
| semantic_skills | +0.244 [+0.174, +0.317] (significant) |
| semantic_fulltext | +0.117 [+0.076, +0.161] (significant) |
| semantic_profile_concat | +0.147 [+0.101, +0.194] (significant) |
| semantic_profile_pooled | +0.154 [+0.109, +0.202] (significant) |
| hybrid_skills_embedding | +0.039 [+0.012, +0.069] (significant) |
| hybrid_no_experience | +0.170 [+0.121, +0.223] (significant) |

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
| semantic_profile_concat | 0.891 [0.823, 0.947] | 0.652 [0.614, 0.688] | 0.944 [0.883, 1.000] | 0.594 [0.548, 0.636] | 0.533 [0.491, 0.571] | 0.870 [0.800, 0.927] |
| semantic_profile_pooled | 0.891 [0.819, 0.951] | 0.682 [0.642, 0.719] | 0.936 [0.858, 1.000] | 0.625 [0.570, 0.678] | 0.567 [0.523, 0.609] | 0.857 [0.770, 0.930] |
| hybrid_skills_embedding | 0.896 [0.846, 0.940] | 0.705 [0.672, 0.739] | 0.950 [0.900, 1.000] | 0.647 [0.600, 0.694] | 0.600 [0.561, 0.640] | 0.877 [0.823, 0.927] |
| hybrid_no_experience | 0.926 [0.888, 0.960] | 0.759 [0.725, 0.791] | 1.000 [1.000, 1.000] | 0.718 [0.668, 0.764] | 0.664 [0.621, 0.705] | 0.897 [0.843, 0.943] |
| hybrid | 0.924 [0.888, 0.955] | 0.728 [0.703, 0.753] | 1.000 [1.000, 1.000] | 0.661 [0.620, 0.700] | 0.620 [0.585, 0.655] | 0.890 [0.840, 0.933] |

Paired difference in nDCG@10 (hybrid minus other ranker, same jobs):

| Compared with | Δ ndcg@10 (95% CI) |
|---|---|
| bm25 | -0.028 [-0.059, +0.001] (not significant) |
| tfidf | -0.043 [-0.078, -0.010] (significant) |
| skill_overlap | +0.041 [+0.012, +0.074] (significant) |
| semantic_skills | +0.091 [+0.048, +0.134] (significant) |
| semantic_fulltext | +0.001 [-0.034, +0.039] (not significant) |
| semantic_profile_concat | +0.033 [-0.011, +0.082] (not significant) |
| semantic_profile_pooled | +0.033 [-0.006, +0.080] (not significant) |
| hybrid_skills_embedding | +0.029 [+0.004, +0.057] (significant) |
| hybrid_no_experience | -0.002 [-0.021, +0.022] (not significant) |

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

