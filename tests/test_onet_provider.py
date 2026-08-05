from pathlib import Path

from app.knowledge_base.providers.onet_provider import ONETProvider


def test_load_onet_provider():

    csv_path = Path("data/onet/raw/software_skills.csv")

    provider = ONETProvider(csv_path)

    skills = provider.load()

    assert len(skills) > 0

    first = skills[0]

    assert first.name == "Adobe Acrobat"

    assert first.category == "software_skill"