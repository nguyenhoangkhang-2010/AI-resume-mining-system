import json
from pathlib import Path


CUSTOM_TAXONOMY = Path(
    "data/taxonomy/source/skills.json"
)

ESCO_SKILLS = Path(
    "data/esco/processed/esco_skills.json"
)

OUTPUT = Path(
    "data/taxonomy/generated/skills.json"
)


def load_json(path):
    with open(
        path,
        encoding="utf-8"
    ) as f:
        return json.load(f)


def flatten_custom(
    data,
    domain=None,
    category=None
):
    result = []
    if isinstance(data, list):
        for skill in data:
            if isinstance(skill, str):
                result.append(
                    {
                        "name": skill,
                        "domain": domain,
                        "category": category,
                        "aliases": [],
                        "source": "CUSTOM"
                    }
                )
            elif isinstance(skill, dict):
                result.append(
                    {
                        "name": skill["name"],
                        "domain": skill.get(
                            "domain",
                            domain
                        ),
                        "category": skill.get(
                            "category",
                            category
                        ),
                        "aliases": skill.get(
                            "aliases",
                            []
                        ),
                        "source": "CUSTOM"
                    }
                )
    elif isinstance(data, dict):
        for key, value in data.items():
            if domain is None:
                result.extend(
                    flatten_custom(
                        value,
                        domain=key
                    )
                )
            else:
                result.extend(
                    flatten_custom(
                        value,
                        domain=domain,
                        category=key
                    )
                )
    return result


def normalize_esco(skills):
    result = []
    for skill in skills:
        result.append(
            {
                "name": skill["name"],
                "domain": "ESCO",
                "category": "ESCO",
                "aliases": skill.get(
                    "aliases",
                    []
                ),
                "source": "ESCO",
                "uri": skill.get(
                    "uri"
                )
            }
        )
    return result


def merge_skills(
    custom,
    esco
):
    merged = {}
    for skill in custom + esco:
        key = skill["name"].lower()
        if key not in merged:
            merged[key] = skill
    return list(
        merged.values()
    )


def main():
    custom = load_json(
        CUSTOM_TAXONOMY
    )
    esco = load_json(
        ESCO_SKILLS
    )
    custom_skills = flatten_custom(
        custom
    )
    esco_skills = normalize_esco(
        esco
    )
    final = merge_skills(
        custom_skills,
        esco_skills
    )
    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True
    )
    with open(
        OUTPUT,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            final,
            f,
            indent=4,
            ensure_ascii=False
        )
    print(
        f"Generated {len(final)} skills"
    )


if __name__ == "__main__":
    main()