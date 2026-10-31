# Evaluation

Offline evaluation of candidate ranking and skill extraction on a synthetic,
seeded dataset.

```bash
python -m scripts.generate_eval_dataset --out data/evaluation/synthetic_v1
python -m scripts.run_evaluation --dataset data/evaluation/synthetic_v1 --out docs/evaluation/synthetic_v1.md
```

`--embedding hashing` runs without downloading the sentence-transformer model
(semantic rows are then not meaningful) and `--skip-extraction` skips the
skill-extraction benchmark. The full report is in
[synthetic_v1.md](synthetic_v1.md). Recommending jobs to candidates is evaluated in
[job_recommendation.md](job_recommendation.md). What the extraction-quality branch changed: [extraction_quality.md](extraction_quality.md). Reranking and the fairness audit: [ranking_quality.md](ranking_quality.md). Evaluation on real CVs (private labels,
aggregate results only) is described in [real_cv_README.md](real_cv_README.md).

## How the data and labels are built

Each synthetic candidate has a latent role family and years of experience.
Relevance labels are derived from those latent attributes only, never from the
skills a candidate lists, so skill-overlap rankers are not scored against labels
they define. Listed skills carry noise: missing core skills, off-role skills,
alias spellings, generic job titles and "keyword stuffers" that list another
role's skills. The dataset is regenerated from its seed in a test, so the
committed files are reproducible.

Two label sets are reported because they answer different questions:
`seniority_aware` (family and years) and `family_only` (family alone).

## Findings from the 2026-10-28 run (seed 42, 30 jobs, 300 candidates)

These are measurements on synthetic data, not real-world accuracy.

Rankers: `hybrid` is the production scoring path (skill coverage,
profile-text embedding, experience). `hybrid_skills_embedding` is the same path
with the earlier skills-only embedding, so their difference is the effect of
the richer embedding text.

| nDCG@10 | seniority-aware labels | family-only labels |
|---|---|---|
| bm25 | 0.784 | 0.952 |
| tfidf | 0.786 | 0.968 |
| hybrid_skills_embedding (before) | 0.855 | 0.896 |
| hybrid (after) | **0.894** | 0.924 |

- **Richer embedding text helps.** Replacing the skills-only embedding with the
  profile text (roles, summary, skills, experience bullets, projects) raises
  hybrid nDCG@10 by +0.039 (95% CI [+0.012, +0.069]) on seniority-aware labels
  and +0.029 ([+0.004, +0.057]) on family-only labels. The embedding alone
  improves more: 0.649 to 0.747 and 0.834 to 0.891.
- **Against text baselines:** with seniority-aware labels the hybrid beats BM25
  (+0.110, [+0.057, +0.164]) and TF-IDF (+0.108, [+0.051, +0.166]). With
  family-only labels it is not distinguishable from BM25 (-0.028,
  [-0.059, +0.001]) and still below TF-IDF (-0.043, [-0.078, -0.010]).
- **The experience component carries much of the seniority result.** Without it
  the hybrid scores 0.724 on seniority-aware labels, below BM25. On
  family-only labels, where seniority is irrelevant, removing it changes
  nothing (0.926 versus 0.924).
- Embedding each section separately and averaging (`semantic_profile_pooled`)
  was no better than one concatenated text (0.740 versus 0.747), so production
  uses the simpler concatenation. The concatenated and the earlier full-text
  variants were chosen between on this same dataset, which slightly favours
  the reported numbers.
- Raising the model's 128-token limit to 256 or 512 changed nothing here, but
  the synthetic profiles are short; real resumes are longer, so the text
  builder keeps per-section character budgets instead.
- **Skill extraction** has precision 0.965 but recall 0.466 (F1 0.628) on the
  evaluated vocabulary. Many modern tools score 0.00 recall (for example
  airflow, azure, gcp, django, graphql, html), which points to gaps in the skill
  taxonomy rather than to the matching logic. This is unchanged by this work.
- With 30 jobs the confidence intervals are wide; differences whose paired
  interval includes 0 should not be read as real.
