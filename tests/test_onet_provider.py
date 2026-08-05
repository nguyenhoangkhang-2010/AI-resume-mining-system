from app.knowledge_base.providers.onet_provider import ONETProvider


def test_onet_provider_load():
    provider = ONETProvider()

    entries = provider.load()

    assert len(entries) > 0
    assert entries[0].category == "essential_skill"