import json

import pytest

from scripts import eval_gate


def run_gate(monkeypatch, tmp_path, measured, baseline, shifts=None, argv=()):
    path = tmp_path / "baseline.json"
    path.write_text(json.dumps({"tolerance": 0.02, "metrics": baseline}), encoding="utf-8")

    monkeypatch.setattr(eval_gate, "MEASURES", [lambda: dict(measured)])
    monkeypatch.setattr(eval_gate, "fairness_shifts", lambda: dict(shifts or {}))
    monkeypatch.setattr("sys.argv", ["eval_gate", "--baseline", str(path), *argv])

    return eval_gate.main(), path


def test_numbers_within_the_tolerance_pass(monkeypatch, tmp_path, capsys):
    code, _ = run_gate(monkeypatch, tmp_path, {"a": 0.89}, {"a": 0.90})

    assert code == 0
    assert "All checks passed" in capsys.readouterr().out


def test_a_drop_beyond_the_tolerance_fails(monkeypatch, tmp_path, capsys):
    code, _ = run_gate(monkeypatch, tmp_path, {"a": 0.85}, {"a": 0.90})

    assert code == 1
    assert "REGRESSION" in capsys.readouterr().out


def test_an_improvement_passes_and_says_so(monkeypatch, tmp_path, capsys):
    code, _ = run_gate(monkeypatch, tmp_path, {"a": 0.95}, {"a": 0.90})

    assert code == 0
    assert "better" in capsys.readouterr().out


def test_a_metric_that_is_no_longer_measured_fails(monkeypatch, tmp_path):
    code, _ = run_gate(monkeypatch, tmp_path, {"a": 0.9}, {"a": 0.9, "gone": 0.9})

    assert code == 1


def test_a_new_metric_without_a_baseline_is_ignored(monkeypatch, tmp_path):
    code, _ = run_gate(monkeypatch, tmp_path, {"a": 0.9, "new": 0.1}, {"a": 0.9})

    assert code == 0


def test_a_score_shift_over_the_limit_fails(monkeypatch, tmp_path, capsys):
    code, _ = run_gate(
        monkeypatch, tmp_path, {"a": 0.9}, {"a": 0.9}, shifts={"fairness.shift.pronoun": 0.4}
    )

    assert code == 1
    assert "fairness.shift.pronoun" in capsys.readouterr().out


def test_update_writes_the_measured_numbers(monkeypatch, tmp_path):
    code, path = run_gate(
        monkeypatch, tmp_path, {"a": 0.91234567}, {"a": 0.5}, argv=("--update",)
    )

    assert code == 0
    assert json.loads(path.read_text(encoding="utf-8"))["metrics"] == {"a": 0.9123}


def test_the_committed_baseline_is_complete_and_sane():
    stored = json.loads(eval_gate.BASELINE.read_text(encoding="utf-8"))

    assert set(stored["metrics"]) == {
        "ranking.family_only.mrr",
        "ranking.family_only.ndcg@10",
        "ranking.seniority_aware.mrr",
        "ranking.seniority_aware.ndcg@10",
        "sections.english_vietnamese.line_accuracy",
        "sections.other_languages.line_accuracy",
    }
    assert all(0.5 < value <= 1.0 for value in stored["metrics"].values())
    assert 0 < stored["tolerance"] <= 0.05


@pytest.mark.parametrize("value, baseline, passed", [(0.88, 0.90, True), (0.879, 0.90, False)])
def test_the_tolerance_edge(value, baseline, passed):
    assert eval_gate.Check("m", value, baseline, 0.02).passed is passed
