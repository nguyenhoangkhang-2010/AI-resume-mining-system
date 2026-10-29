from app.knowledge_base.bootstrap import build_taxonomy_repository

import pytest

pytestmark = pytest.mark.requires_onet




def test_bootstrap_builds_repository():
    repository = build_taxonomy_repository()

    entries = repository.load_all()

    assert isinstance(entries, list)