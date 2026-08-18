import json
from pathlib import Path


SOURCE = Path(
    "data/taxonomy/source/skills.json"
)

OUTPUT = Path(
    "data/taxonomy/generated/skills.json"
)


def flatten_taxonomy(data):
    result = []
    if isinstance(data, list):
        for skill in data:
            result.append(
                {
                    "name": skill["name"],
                    "domain": skill.get("domain"),
                    "category": skill.get("category"),
                    "aliases": skill.get(
                        "aliases",
                        []
                    )
                }
            )
    return result



def main():
    with open(
        SOURCE,
        encoding="utf-8"
    ) as f:
        taxonomy = json.load(f)
    skills = flatten_taxonomy(taxonomy)
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
            skills,
            f,
            indent=4,
            ensure_ascii=False
        )
    print(
        f"Generated {len(skills)} skills"
    )


if __name__ == "__main__":
    main()