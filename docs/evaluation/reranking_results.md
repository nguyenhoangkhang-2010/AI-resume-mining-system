# Does cross-encoder reranking help?

Generated 2026-10-31 by `scripts/evaluate_reranking.py`. Reranker: `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1`.

Synthetic data: labels come from the latent role family and years of experience, so the numbers show behaviour under that noise model, not hiring accuracy.

## Development dataset (used to choose the blend weight)

30 jobs, 300 candidates (seed 42); the top 50 of the first stage are reranked.

### Labels: `seniority_aware`

Mean over jobs with 95% bootstrap interval.

| Ranker | ndcg@10 | ndcg@50 | mrr | map | precision@10 |
|---|---|---|---|---|---|
| hybrid | 0.894 [0.851, 0.934] | 0.778 [0.746, 0.806] | 1.000 [1.000, 1.000] | 0.688 [0.643, 0.727] | 0.877 [0.823, 0.927] |
| hybrid + rerank, weight 0.25 | 0.861 [0.811, 0.906] | 0.771 [0.738, 0.799] | 1.000 [1.000, 1.000] | 0.672 [0.627, 0.713] | 0.843 [0.783, 0.900] |
| hybrid + rerank, weight 0.5 | 0.821 [0.768, 0.870] | 0.757 [0.722, 0.787] | 0.978 [0.933, 1.000] | 0.641 [0.600, 0.679] | 0.810 [0.750, 0.863] |
| hybrid + rerank, weight 0.75 | 0.775 [0.720, 0.828] | 0.742 [0.708, 0.774] | 0.944 [0.878, 1.000] | 0.615 [0.575, 0.653] | 0.763 [0.707, 0.813] |
| hybrid + rerank, weight 1 | 0.708 [0.651, 0.760] | 0.724 [0.690, 0.755] | 0.878 [0.794, 0.950] | 0.588 [0.549, 0.626] | 0.693 [0.637, 0.743] |

Paired difference in nDCG@10, `hybrid` minus the other ranker (same jobs; positive means hybrid is better):

| Compared with | Δ ndcg@10 (95% CI) |
|---|---|
| hybrid + rerank, weight 0.25 | +0.033 [+0.007, +0.063] (significant) |
| hybrid + rerank, weight 0.5 | +0.073 [+0.033, +0.114] (significant) |
| hybrid + rerank, weight 0.75 | +0.119 [+0.078, +0.161] (significant) |
| hybrid + rerank, weight 1 | +0.186 [+0.142, +0.232] (significant) |

### Labels: `family_only`

Mean over jobs with 95% bootstrap interval.

| Ranker | ndcg@10 | ndcg@50 | mrr | map | precision@10 |
|---|---|---|---|---|---|
| hybrid | 0.924 [0.888, 0.955] | 0.728 [0.703, 0.753] | 1.000 [1.000, 1.000] | 0.661 [0.620, 0.700] | 0.890 [0.840, 0.933] |
| hybrid + rerank, weight 0.25 | 0.908 [0.867, 0.945] | 0.725 [0.699, 0.751] | 1.000 [1.000, 1.000] | 0.654 [0.613, 0.692] | 0.870 [0.813, 0.920] |
| hybrid + rerank, weight 0.5 | 0.876 [0.825, 0.919] | 0.715 [0.687, 0.741] | 0.978 [0.933, 1.000] | 0.633 [0.593, 0.671] | 0.840 [0.780, 0.893] |
| hybrid + rerank, weight 0.75 | 0.846 [0.792, 0.894] | 0.706 [0.678, 0.732] | 0.944 [0.878, 1.000] | 0.617 [0.578, 0.655] | 0.813 [0.753, 0.867] |
| hybrid + rerank, weight 1 | 0.806 [0.750, 0.858] | 0.697 [0.668, 0.726] | 0.878 [0.794, 0.950] | 0.604 [0.564, 0.642] | 0.767 [0.707, 0.820] |

Paired difference in nDCG@10, `hybrid` minus the other ranker (same jobs; positive means hybrid is better):

| Compared with | Δ ndcg@10 (95% CI) |
|---|---|
| hybrid + rerank, weight 0.25 | +0.016 [-0.007, +0.042] (not significant) |
| hybrid + rerank, weight 0.5 | +0.049 [+0.010, +0.090] (significant) |
| hybrid + rerank, weight 0.75 | +0.078 [+0.035, +0.125] (significant) |
| hybrid + rerank, weight 1 | +0.119 [+0.071, +0.171] (significant) |

## Test dataset (not used to choose anything)

60 jobs, 300 candidates (seed 7); the top 50 of the first stage are reranked.

### Labels: `seniority_aware`

Mean over jobs with 95% bootstrap interval.

| Ranker | ndcg@10 | ndcg@50 | mrr | map | precision@10 |
|---|---|---|---|---|---|
| hybrid | 0.880 [0.851, 0.906] | 0.789 [0.768, 0.809] | 0.983 [0.958, 1.000] | 0.710 [0.681, 0.736] | 0.870 [0.837, 0.900] |
| hybrid + rerank, weight 0.25 | 0.855 [0.823, 0.886] | 0.779 [0.757, 0.799] | 0.983 [0.958, 1.000] | 0.681 [0.652, 0.711] | 0.830 [0.793, 0.867] |
| hybrid + rerank, weight 0.5 | 0.812 [0.776, 0.849] | 0.764 [0.743, 0.785] | 0.983 [0.958, 1.000] | 0.647 [0.616, 0.678] | 0.775 [0.730, 0.822] |
| hybrid + rerank, weight 0.75 | 0.760 [0.718, 0.803] | 0.748 [0.725, 0.770] | 0.944 [0.900, 0.983] | 0.624 [0.592, 0.657] | 0.728 [0.683, 0.777] |
| hybrid + rerank, weight 1 | 0.707 [0.663, 0.751] | 0.732 [0.709, 0.755] | 0.881 [0.822, 0.934] | 0.604 [0.571, 0.637] | 0.688 [0.642, 0.735] |

Paired difference in nDCG@10, `hybrid` minus the other ranker (same jobs; positive means hybrid is better):

| Compared with | Δ ndcg@10 (95% CI) |
|---|---|
| hybrid + rerank, weight 0.25 | +0.025 [+0.000, +0.049] (significant) |
| hybrid + rerank, weight 0.5 | +0.069 [+0.030, +0.107] (significant) |
| hybrid + rerank, weight 0.75 | +0.120 [+0.073, +0.165] (significant) |
| hybrid + rerank, weight 1 | +0.173 [+0.125, +0.221] (significant) |

### Labels: `family_only`

Mean over jobs with 95% bootstrap interval.

| Ranker | ndcg@10 | ndcg@50 | mrr | map | precision@10 |
|---|---|---|---|---|---|
| hybrid | 0.920 [0.896, 0.940] | 0.751 [0.732, 0.768] | 0.983 [0.958, 1.000] | 0.705 [0.677, 0.730] | 0.893 [0.862, 0.918] |
| hybrid + rerank, weight 0.25 | 0.902 [0.880, 0.925] | 0.745 [0.726, 0.763] | 0.983 [0.958, 1.000] | 0.685 [0.657, 0.712] | 0.862 [0.828, 0.895] |
| hybrid + rerank, weight 0.5 | 0.877 [0.846, 0.905] | 0.737 [0.717, 0.755] | 0.983 [0.958, 1.000] | 0.662 [0.633, 0.690] | 0.827 [0.783, 0.868] |
| hybrid + rerank, weight 0.75 | 0.840 [0.804, 0.874] | 0.728 [0.707, 0.748] | 0.956 [0.917, 0.992] | 0.647 [0.618, 0.676] | 0.785 [0.742, 0.827] |
| hybrid + rerank, weight 1 | 0.805 [0.765, 0.843] | 0.719 [0.698, 0.739] | 0.901 [0.846, 0.950] | 0.634 [0.604, 0.663] | 0.757 [0.712, 0.800] |

Paired difference in nDCG@10, `hybrid` minus the other ranker (same jobs; positive means hybrid is better):

| Compared with | Δ ndcg@10 (95% CI) |
|---|---|
| hybrid + rerank, weight 0.25 | +0.018 [-0.001, +0.038] (not significant) |
| hybrid + rerank, weight 0.5 | +0.044 [+0.012, +0.076] (significant) |
| hybrid + rerank, weight 0.75 | +0.080 [+0.041, +0.120] (significant) |
| hybrid + rerank, weight 1 | +0.116 [+0.073, +0.159] (significant) |

