import pandas as pd
import json
from pathlib import Path
from loguru import logger


INPUT = Path(
    "data/esco/raw/skills_en.csv"
)

OUTPUT = Path(
    "data/esco/processed/esco_skills.json"
)


def process_esco():
    logger.info("Loading ESCO CSV...")
    df = pd.read_csv(
        INPUT
    )
    # chỉ lấy skill/knowledge concepts
    df = df[
        df["conceptType"]
        == "KnowledgeSkillCompetence"
    ]
    skills = []
    for _, row in df.iterrows():
        skill = {
            "name": row["preferredLabel"],
            "source": "ESCO",
            "uri": row["conceptUri"],
            "definition": row["definition"]
            if pd.notna(row["definition"])
            else "",
            "aliases": []
        }
        skills.append(skill)
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
    logger.success(
        f"Processed {len(skills)} ESCO skills"
    )



if __name__ == "__main__":
    process_esco()