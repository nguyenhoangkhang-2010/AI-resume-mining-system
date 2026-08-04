# Skill Normalization Layer

## Purpose

The Skill Normalization Layer converts extracted skills into canonical representations before matching.

Example

Raw Skill

```
PYTHON3
```

↓

Canonical Skill

```
python
```

---

## Pipeline

```
Unicode
    ↓
Trim Whitespace
    ↓
Remove Punctuation
    ↓
Lowercase
    ↓
Alias Resolution
```

---

## Components

### SkillNormalizer

Responsible for executing all normalization rules sequentially.

### NormalizationRule

Abstract interface implemented by every rule.

### Implemented Rules

- UnicodeNormalizationRule
- TrimWhitespaceRule
- PunctuationNormalizationRule
- CaseNormalizationRule
- AliasNormalizationRule

---

## Repository

AliasNormalizationRule never accesses JSON directly.

Instead it depends on

```
SkillAliasRepository
```

Current implementation

```
JsonSkillAliasRepository
```

Future implementations may include

- PostgreSQL
- Redis
- Elasticsearch
- REST API

without modifying normalization logic.

---

## How to add a new rule

1. Create a class implementing

```
NormalizationRule
```

2. Register it inside

```
build_skill_normalizer()
```

3. Add unit tests.

---

## Design Principles

- Dependency Injection
- Single Responsibility
- Open/Closed Principle
- Extensible Pipeline
- Repository Pattern