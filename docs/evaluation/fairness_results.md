# Counterfactual fairness audit

Generated 2026-10-31 by `scripts/audit_fairness.py`. 30 jobs, 300 synthetic candidates (seed 42); the top 10 per job are selected; 8 random splits of the candidates into groups A and B. 

## What was changed

- **pronoun**: A sentence about mentoring in the summary, in the third person with 'She' (A) or 'He' (B).
- **affinity group**: A line about a society: a women-in-engineering society (A) or a general engineering society (B).
- **name, Vietnamese**: The summary starts with a Vietnamese name (A) or an English one (B).
- **name, Arabic**: The summary starts with an Arabic name (A) or an English one (B).
- **career break**: Two years without work before the last job (A) or none (B); the jobs keep their lengths, so the years of experience are the same.
- **CV language**: The titles and sentences of the profile are in Vietnamese (A) or English (B); skill names stay as written. The job is in English.

## Results

### Before: the text is embedded as written

| Change | Ranker | Selection ratio A/B (95% interval) | Detectable | Below 4/5 | Mean score shift A-B (95% interval) | Candidates moved by 1 point or more |
|---|---|---|---|---|---|---|
| pronoun | hybrid | 0.89 [0.81, 0.97] | yes | no | -0.32 [-0.39, -0.25] | 1.5% |
| affinity group | hybrid | 0.87 [0.80, 0.95] | yes | no | -0.36 [-0.45, -0.27] | 7.1% |
| name, Vietnamese | hybrid | 0.98 [0.90, 1.06] | no | no | -0.26 [-0.59, +0.05] | 48.0% |
| name, Arabic | hybrid | 0.84 [0.77, 0.91] | yes | no | -0.79 [-1.05, -0.55] | 51.0% |
| career break | hybrid | 0.96 [0.88, 1.04] | no | no | +0.00 [+0.00, +0.00] | 0.0% |
| CV language | hybrid | 0.91 [0.83, 0.99] | yes | no | -0.52 [-0.71, -0.32] | 49.0% |

### After: pronouns, titles and the person's name are removed first (profile-v2)

| Change | Ranker | Selection ratio A/B (95% interval) | Detectable | Below 4/5 | Mean score shift A-B (95% interval) | Candidates moved by 1 point or more |
|---|---|---|---|---|---|---|
| pronoun | hybrid | 0.96 [0.89, 1.05] | no | no | +0.00 [+0.00, +0.00] | 0.0% |
| affinity group | hybrid | 0.87 [0.80, 0.95] | yes | no | -0.36 [-0.45, -0.27] | 7.1% |
| name, Vietnamese | hybrid | 0.96 [0.88, 1.04] | no | no | +0.00 [+0.00, +0.00] | 0.0% |
| name, Arabic | hybrid | 0.96 [0.88, 1.04] | no | no | +0.00 [+0.00, +0.00] | 0.0% |
| career break | hybrid | 0.96 [0.88, 1.04] | no | no | +0.00 [+0.00, +0.00] | 0.0% |
| CV language | hybrid | 0.91 [0.83, 0.99] | yes | no | -0.52 [-0.71, -0.32] | 49.0% |

Selection ratio: selection rate of group A divided by that of group B; 1.0 means no difference, and the groups are random halves of the same candidates, so any difference comes from the change. *Detectable* means the interval of the ratio excludes 1; *Below 4/5* means the ratio is outside 0.8 to 1.25. Score shift is in points of the 0-100 match score. A ratio near 0.96 with no score shift (career break, and every row after the fix) is the imbalance of the random splits, not an effect: its interval contains 1.
