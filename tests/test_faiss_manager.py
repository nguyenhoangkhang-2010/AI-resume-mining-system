import threading

import numpy as np
import pytest

from app.database.vector_db.faiss_manager import FaissManager


DIMENSION = 8


def unit(position):
    vector = np.zeros(DIMENSION, dtype=np.float32)
    vector[position % DIMENSION] = 1.0
    return vector


@pytest.fixture
def manager(tmp_path):
    return FaissManager.for_path(tmp_path / "candidate.index", dimension=DIMENSION)


def test_adding_the_same_id_twice_keeps_one_vector(manager):
    manager.add_vector(5, unit(0))
    manager.add_vector(5, unit(1))

    assert manager.ntotal == 1
    assert manager.ids() == {5}

    _, ids = manager.search(unit(1), 1)

    assert ids[0] == 5


def test_re_adding_replaces_the_stored_vector(manager):
    manager.add_vector(5, unit(0))
    manager.add_vector(5, unit(3))

    scores, ids = manager.search(unit(3), 1)

    assert scores[0] == pytest.approx(1.0)


def test_remove_ids(manager):
    manager.add_vector(1, unit(0))
    manager.add_vector(2, unit(1))

    assert manager.remove_ids([1, 99]) == 1
    assert manager.ids() == {2}
    assert manager.remove_ids([]) == 0


def test_ids_of_empty_index(manager):
    assert manager.ids() == set()


def test_changes_survive_reload(tmp_path):
    first = FaissManager.for_path(tmp_path / "i.index", dimension=DIMENSION)
    first.add_vector(1, unit(0))
    first.add_vector(2, unit(1))
    first.remove_ids([1])

    second = FaissManager.for_path(tmp_path / "i.index", dimension=DIMENSION)

    assert second.ids() == {2}


def test_save_every_batches_writes_and_flush_persists(tmp_path):
    path = tmp_path / "i.index"
    manager = FaissManager.for_path(path, dimension=DIMENSION, save_every=3)

    saves = []
    original = manager.save_index

    def counting_save():
        saves.append(1)
        original()

    manager.save_index = counting_save

    manager.add_vector(1, unit(0))
    manager.add_vector(2, unit(1))

    assert saves == []
    assert not path.exists()

    manager.add_vector(3, unit(2))

    assert len(saves) == 1
    assert path.exists()

    manager.add_vector(4, unit(3))
    manager.flush()

    assert len(saves) == 2
    assert FaissManager.for_path(path, dimension=DIMENSION).ids() == {1, 2, 3, 4}


def test_flush_without_changes_does_not_write(manager):
    manager.flush()

    assert not manager.index_path.exists()


def test_save_leaves_no_temporary_file(manager):
    manager.add_vector(1, unit(0))

    assert manager.index_path.exists()
    assert not manager.index_path.with_suffix(".tmp").exists()


def test_concurrent_adds_lose_nothing(manager):
    errors = []

    def worker(offset):
        try:
            for i in range(25):
                manager.add_vector(offset * 100 + i, unit(i))
        except Exception as exc:  # pragma: no cover - failure path
            errors.append(exc)

    threads = [threading.Thread(target=worker, args=(n,)) for n in range(8)]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    assert errors == []
    assert manager.ntotal == 200
    assert len(manager.ids()) == 200


def test_search_while_adding_does_not_fail(manager):
    manager.add_vector(0, unit(0))

    errors = []
    stop = threading.Event()

    def searcher():
        try:
            while not stop.is_set():
                manager.search(unit(0), 3)
        except Exception as exc:  # pragma: no cover - failure path
            errors.append(exc)

    thread = threading.Thread(target=searcher)
    thread.start()

    for i in range(1, 60):
        manager.add_vector(i, unit(i))

    stop.set()
    thread.join()

    assert errors == []
    assert manager.ntotal == 60


def test_shutdown_without_singleton_is_a_noop(monkeypatch):
    monkeypatch.setattr(FaissManager, "_instance", None)

    FaissManager.shutdown()
