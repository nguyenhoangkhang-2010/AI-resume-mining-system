import threading
from types import SimpleNamespace

import numpy as np
import pytest

import app.bootstrap as bootstrap
from app.core.config.settings import settings
from app.embeddings.services import embedding_service
from app.embeddings.services.embedding_service import EmbeddingService, embedding_cache


class CountingModel:
    def __init__(self):
        self.calls = 0

    def encode(self, text, **kwargs):
        self.calls += 1

        return np.array([float(len(text)), 1.0], dtype=np.float32)


@pytest.fixture
def service(monkeypatch):
    model = CountingModel()
    instance = EmbeddingService.__new__(EmbeddingService)
    instance.model = model
    embedding_cache.clear()
    monkeypatch.setattr(settings, "EMBEDDING_CACHE_SIZE", 3)

    yield instance, model

    embedding_cache.clear()


def test_the_same_text_is_embedded_once(service):
    instance, model = service

    first = instance.generate_embedding("a job")
    second = instance.generate_embedding("a job")

    assert model.calls == 1
    assert np.array_equal(first, second)


def test_a_caller_that_changes_the_vector_does_not_change_the_cache(service):
    instance, _ = service

    vector = instance.generate_embedding("text")
    vector[:] = 0
    again = instance.generate_embedding("text")
    again[:] = 0

    assert instance.generate_embedding("text")[1] == 1.0


def test_the_least_recently_used_text_is_dropped_first(service):
    instance, model = service

    for text in ("a", "bb", "ccc"):
        instance.generate_embedding(text)

    instance.generate_embedding("a")  # now "bb" is the oldest
    instance.generate_embedding("dddd")  # pushes "bb" out
    calls = model.calls

    instance.generate_embedding("a")
    instance.generate_embedding("ccc")
    assert model.calls == calls

    instance.generate_embedding("bb")
    assert model.calls == calls + 1


def test_a_size_of_zero_turns_the_cache_off(service, monkeypatch):
    instance, model = service
    monkeypatch.setattr(settings, "EMBEDDING_CACHE_SIZE", 0)

    instance.generate_embedding("x")
    instance.generate_embedding("x")

    assert model.calls == 2


def test_a_failing_model_caches_nothing(service):
    instance, _ = service

    def broken(text, **kwargs):
        raise RuntimeError("no model")

    instance.model = SimpleNamespace(encode=broken)

    with pytest.raises(RuntimeError):
        instance.generate_embedding("x")

    assert len(embedding_cache) == 0


def test_threads_can_use_the_cache_at_the_same_time(service):
    instance, _ = service
    errors = []

    def work(number):
        try:
            for i in range(50):
                instance.generate_embedding(f"text {(number + i) % 5}")
        except Exception as error:
            errors.append(error)

    threads = [threading.Thread(target=work, args=(n,)) for n in range(8)]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    assert errors == [] and len(embedding_cache) <= 3


def test_the_module_exposes_one_shared_cache():
    assert embedding_service.embedding_cache is embedding_cache


# ------------------------------------------------------------------- warm-up


def test_warm_up_sets_the_flag_when_it_finishes(monkeypatch):
    monkeypatch.setattr(bootstrap, "warm_up", lambda: None)
    state = SimpleNamespace()

    bootstrap.start_warm_up(state).join(timeout=5)

    assert state.warm is True


def test_a_failing_warm_up_does_not_keep_the_api_unready(monkeypatch):
    def fail():
        raise RuntimeError("taxonomy missing")

    monkeypatch.setattr(bootstrap, "warm_up", fail)
    state = SimpleNamespace()

    bootstrap.start_warm_up(state).join(timeout=5)

    assert state.warm is True


def test_the_flag_is_false_while_the_warm_up_runs(monkeypatch):
    release = threading.Event()
    monkeypatch.setattr(bootstrap, "warm_up", lambda: release.wait(timeout=5))
    state = SimpleNamespace()

    thread = bootstrap.start_warm_up(state)
    assert state.warm is False

    release.set()
    thread.join(timeout=5)
    assert state.warm is True
