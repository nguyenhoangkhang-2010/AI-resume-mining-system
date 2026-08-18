from pathlib import Path

from app.knowledge_base.providers.onet_provider import ONETProvider


def test_onet_provider_load():
    provider = ONETProvider()

    entries = provider.load()

    assert len(entries) > 0


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


def test_load_knowledge():
    provider = ONETProvider()

    entries = provider.load()

    knowledge = [
        entry
        for entry in entries
        if entry.category == "knowledge"
    ]

    assert len(knowledge) > 0


def test_load_abilities():
    provider = ONETProvider()

    entries = provider.load()

    abilities = [
        entry
        for entry in entries
        if entry.category == "ability"
    ]

    assert len(abilities) > 0
    assert abilities[0].id
    assert abilities[0].name
    
def test_load_work_activities():
    provider = ONETProvider()

    entries = provider.load()

    activities = [
        entry
        for entry in entries
        if entry.category == "work_activity"
    ]

    assert len(activities) > 0
    assert activities[0].id
    assert activities[0].name
    
    
def test_load_work_styles():
    provider = ONETProvider()

    entries = provider.load()

    styles = [
        entry
        for entry in entries
        if entry.category == "work_style"
    ]

    assert len(styles) > 0
    assert styles[0].id
    assert styles[0].name