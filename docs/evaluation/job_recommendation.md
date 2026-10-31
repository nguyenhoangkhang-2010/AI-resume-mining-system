# Job recommendation on the synthetic dataset

Generated 2026-10-31 by `scripts/evaluate_job_recommendation.py` (dataset seed 42, embedding: real).

- Candidates: 300 (each ranks 30 jobs)

## Limitations

- The data is synthetic; labels come from latent attributes (role family, years of experience), so the numbers measure behaviour under that noise model, not real hiring.
- Each candidate chooses among only 30 jobs, so the metrics are computed at small cutoffs; the `random` row shows what ordering the jobs at random scores. Candidates with no relevant job are left out.
- BM25 is not evaluated: its scores are not comparable between jobs.
- `hybrid` is the production scoring path. `hybrid_no_experience` drops the experience component.

## Ranking jobs for a candidate

### Labels: `seniority_aware`

Labels combine role family and seniority (0-3), as on the recruiter side: a job is graded 3 when it is in the candidate's family and the candidate has enough experience for it.

Mean over 300 candidates with at least one relevant job, with 95% bootstrap confidence intervals.

| Ranker | ndcg@3 | ndcg@5 | mrr | map | recall@5 | precision@3 |
|---|---|---|---|---|---|---|
| random | 0.152 [0.131, 0.175] | 0.167 [0.147, 0.185] | 0.295 [0.264, 0.329] | 0.216 [0.203, 0.231] | 0.157 [0.135, 0.179] | 0.121 [0.101, 0.143] |
| tfidf | 0.577 [0.537, 0.616] | 0.615 [0.581, 0.647] | 0.691 [0.650, 0.730] | 0.623 [0.591, 0.654] | 0.644 [0.606, 0.679] | 0.524 [0.481, 0.564] |
| skill_overlap | 0.597 [0.559, 0.637] | 0.613 [0.579, 0.649] | 0.715 [0.674, 0.754] | 0.613 [0.580, 0.647] | 0.618 [0.581, 0.656] | 0.541 [0.500, 0.583] |
| semantic_profile_concat | 0.527 [0.486, 0.567] | 0.537 [0.503, 0.571] | 0.658 [0.616, 0.699] | 0.545 [0.510, 0.578] | 0.536 [0.500, 0.572] | 0.480 [0.437, 0.522] |
| hybrid_no_experience | 0.642 [0.606, 0.678] | 0.662 [0.630, 0.693] | 0.754 [0.715, 0.792] | 0.650 [0.618, 0.683] | 0.675 [0.641, 0.710] | 0.591 [0.552, 0.631] |
| hybrid | 0.705 [0.669, 0.739] | 0.709 [0.678, 0.739] | 0.810 [0.775, 0.845] | 0.701 [0.670, 0.731] | 0.709 [0.675, 0.742] | 0.631 [0.593, 0.668] |

Paired difference in nDCG@3 (hybrid minus other ranker, same candidates):

| Compared with | Δ ndcg@3 (95% CI) |
|---|---|
| random | +0.552 [+0.512, +0.591] (significant) |
| tfidf | +0.127 [+0.084, +0.170] (significant) |
| skill_overlap | +0.108 [+0.088, +0.128] (significant) |
| semantic_profile_concat | +0.178 [+0.139, +0.218] (significant) |
| hybrid_no_experience | +0.063 [+0.047, +0.079] (significant) |

### Labels: `family_only`

Labels depend only on role family (0-2); seniority is ignored.

Mean over 300 candidates with at least one relevant job, with 95% bootstrap confidence intervals.

| Ranker | ndcg@3 | ndcg@5 | mrr | map | recall@5 | precision@3 |
|---|---|---|---|---|---|---|
| random | 0.243 [0.219, 0.268] | 0.239 [0.220, 0.258] | 0.349 [0.316, 0.384] | 0.253 [0.241, 0.265] | 0.165 [0.146, 0.182] | 0.170 [0.146, 0.196] |
| tfidf | 0.685 [0.645, 0.724] | 0.667 [0.633, 0.698] | 0.752 [0.713, 0.789] | 0.692 [0.659, 0.721] | 0.609 [0.573, 0.641] | 0.636 [0.592, 0.679] |
| skill_overlap | 0.728 [0.692, 0.764] | 0.692 [0.661, 0.723] | 0.817 [0.783, 0.853] | 0.706 [0.677, 0.737] | 0.615 [0.581, 0.649] | 0.674 [0.633, 0.714] |
| semantic_profile_concat | 0.678 [0.640, 0.716] | 0.636 [0.603, 0.669] | 0.764 [0.725, 0.803] | 0.643 [0.611, 0.674] | 0.554 [0.519, 0.591] | 0.616 [0.574, 0.658] |
| hybrid_no_experience | 0.785 [0.753, 0.819] | 0.747 [0.719, 0.776] | 0.880 [0.849, 0.911] | 0.758 [0.730, 0.786] | 0.675 [0.644, 0.707] | 0.737 [0.701, 0.774] |
| hybrid | 0.774 [0.742, 0.806] | 0.731 [0.703, 0.760] | 0.874 [0.844, 0.905] | 0.738 [0.711, 0.766] | 0.652 [0.621, 0.683] | 0.721 [0.686, 0.758] |

Paired difference in nDCG@3 (hybrid minus other ranker, same candidates):

| Compared with | Δ ndcg@3 (95% CI) |
|---|---|
| random | +0.531 [+0.488, +0.572] (significant) |
| tfidf | +0.089 [+0.045, +0.132] (significant) |
| skill_overlap | +0.046 [+0.028, +0.064] (significant) |
| semantic_profile_concat | +0.095 [+0.055, +0.137] (significant) |
| hybrid_no_experience | -0.011 [-0.020, -0.002] (significant) |

