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
[synthetic_v1.md](synthetic_v1.md).

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

- **With seniority-aware labels** the production hybrid scorer reaches nDCG@10
  0.855 against 0.784 for BM25 (paired difference +0.072, 95% CI
  [+0.006, +0.134]); the gap to TF-IDF is not significant. The gain comes from
  the experience component: the hybrid without it scores 0.680, below BM25.
- **With family-only labels** the hybrid is significantly *worse* than BM25
  and TF-IDF (nDCG@10 0.896 versus 0.952 and 0.968). Its skills-only embedding
  is the weakest ranker in both label sets (0.649 and 0.834).
- Embedding the full profile text instead of just the skill list
  (`semantic_fulltext`) beats the skills-only embedding on both label sets
  (0.777 and 0.923), which supports enriching the embedding input.
- **Skill extraction** has precision 0.965 but recall 0.466 (F1 0.628) on the
  evaluated vocabulary. Many modern tools score 0.00 recall (for example
  airflow, azure, gcp, django, graphql, html), which points to gaps in the skill
  taxonomy rather than to the matching logic.
- With 30 jobs the confidence intervals are wide; differences whose paired
  interval includes 0 should not be read as real.
