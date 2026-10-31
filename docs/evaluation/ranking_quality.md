# Ranking quality: reranking and fairness

Two questions about the ranking that was already measured
([synthetic_v1.md](synthetic_v1.md)): does a second, heavier stage improve it,
and does it treat candidates equally when only something irrelevant differs?
The first answer is no; the second found two small problems, one of which is
fixed.

## 1. Cross-encoder reranking: no gain, left off

**What was built.** After the hybrid score, the best `RERANKER_TOP_N` candidates
(default 50, the whole retrieved list) are rescored by a cross-encoder that
reads the job text and the profile text together, and the final score is
`(1 - w) * hybrid + w * cross-encoder` (cross-encoder scaled 0 to 100 over the
window). A failing model leaves the ranking as it was. It is off by default
(`RERANKER_ENABLED=false`), adds `score_breakdown.rerank_score` to the result,
and uses `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1` (multilingual, 470 MB)
([cross_encoder_reranker.py](../../app/matching/reranking/cross_encoder_reranker.py)).

**Measured** ([reranking_results.md](reranking_results.md),
`python -m scripts.evaluate_reranking`): the weight was to be chosen on the
development set (30 jobs) and reported on a fresh test set (60 jobs, other
seed). Every weight is worse than the hybrid ranker alone on both label sets,
and the loss grows with the weight:

| Test set, nDCG@10 | seniority-aware | family-only |
|---|---|---|
| hybrid | 0.880 | 0.920 |
| + rerank, weight 0.25 | 0.855 | 0.902 |
| + rerank, weight 0.5 | 0.812 | 0.877 |
| + rerank, weight 1.0 (cross-encoder alone) | 0.707 | 0.805 |

The paired differences are significant for 0.5 and above. The default weight is
therefore the smallest tried (0.25), which loses the least, and the stage stays
disabled.

**Why it probably fails here, and why that is limited evidence.** The model was
trained to match questions to passages. The synthetic profiles are templated
and the labels depend on the role family and on years of experience; the
profile text does not carry dates, so the cross-encoder cannot see seniority,
and on family-only labels it is still weaker than BM25 (0.805 against 0.95 on the
development set). A model fine-tuned on resume-job pairs, or real CVs with
real prose, could behave differently; neither was available. This result says
"not for this model on this data", not "reranking does not work".

## 2. Fairness audit

**Method** ([fairness.py](../../app/evaluation/fairness.py),
`python -m scripts.audit_fairness`). Counterfactual pairs: the same synthetic
candidates, with the same skills and years, differing by one detail that should
not matter. Half of the candidates, chosen at random, get one version of the
detail (group A) and the rest the other (B). The ranker picks the top 10 per
job and the audit compares selection rates (A divided by B; the groups are
random, so an unbiased ranker gives 1.0) and the score of the same candidate
as A and as B. Eight random splits, 30 jobs, bootstrap intervals.

**Before** ([fairness_results.md](fairness_results.md)):

| Change | Selection ratio A/B | Candidates moved by 1 point or more |
|---|---|---|
| "She" instead of "He" in a summary sentence | 0.89, detectable | 1.5% |
| women-in-engineering society line | 0.87, detectable | 7.1% |
| a Vietnamese name in the summary instead of an English one | 0.98 | 48% |
| an Arabic name instead of an English one | 0.84, detectable | 51% |
| a two-year career break (same years worked) | 0.96 | 0% |
| CV written in Vietnamese instead of English (job in English) | 0.91, detectable | 49% |

No ratio fell below the four-fifths line (0.8), but several differences were
real and not chance, and names moved the scores of half the candidates: the
embedding reads every word of the summary, including a name or a pronoun.

**Fix** ([neutral_text.py](../../app/matching/neutral_text.py)): gendered
pronouns and titles (English and Vietnamese) and the person's own name are
taken out of the text before it is embedded; `EMBEDDING_VERSION` is now
`profile-v2`. After it, pronoun and both name changes give a score shift of
exactly 0.00 and ratios of 0.96 with intervals around 1 (the 0.96 is the
imbalance of the random splits, the same as for the career break, which was
never affected).

**Still open.**

- *Affinity line* (0.87, 7% of candidates moved): "women in engineering society"
  is content, not a pronoun. Removing group memberships by pattern would be
  guesswork, and some of them (a coding society) say something about skills.
- *CV language* (0.91, half the candidates move by about half a point on
  average): a Vietnamese CV is scored a little lower against an English job.
  Skills are matched as written, so the loss comes from the embedding of the
  sentences. Not fixed; a multilingual embedding that aligns the languages
  better is the route.
- The audit covers changes someone thought of. It does not show bias that
  exists only in real CVs, it uses the hybrid scorer with the production
  embedding model, and the labels themselves are not audited.
- The reranker was not audited (it is off, and 90,000 cross-encoder runs per
  audit are slow on CPU).

## What to do after pulling this change

The text that is embedded changed, so the stored vectors of candidates are
stale: run `python -m scripts.reindex_candidates` (API stopped; back up first).
Until then the API logs a warning for every match that uses older vectors.
