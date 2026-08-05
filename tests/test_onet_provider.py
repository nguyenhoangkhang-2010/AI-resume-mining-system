from app.knowledge_base.providers.onet_provider import ONETProvider

from pathlib import Path

from app.knowledge_base.providers.onet_provider import ONETProvider


def test_onet_provider_load():
    provider = ONETProvider()

    entries = provider.load()

    assert len(entries) > 0
    assert entries[0].category == "essential_skill"


def test_load_essential_skills():
    provider = ONETProvider()

    entries = provider.load()

    assert len(entries) > 0
    assert entries[0].category == "essential_skill"


def test_load_software_skills():
    csv_path = (
        Path(__file__).resolve().parents[1]
        / "data"
        / "onet"
        / "raw"
        / "software_skills.csv"
    )

    provider = ONETProvider(
        {
            "software_skill": csv_path,
        }
    )

    entries = provider._load_entries(
        csv_path,
        "software_skill",
    )

    assert len(entries) > 0
    assert entries[0].category == "software_skill"