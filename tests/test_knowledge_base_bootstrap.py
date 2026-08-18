from app.knowledge_base.bootstrap import build_taxonomy_repository


def test_bootstrap_builds_repository():
    repository = build_taxonomy_repository()

    entries = repository.load_all()

    assert isinstance(entries, list)