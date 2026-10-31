import json

import pytest

from app.evaluation.cv_industries import IndustryCorpusBuilder
from app.evaluation.field_eval import FIELDS
from app.evaluation.real_cv_scoring import (
    CORE_FIELDS,
    CVResult,
    bootstrap_interval,
    core_f1,
    groups,
    report,
    score_cv,
    section_presence,
    weakest,
)
from app.evaluation.real_cvs import (
    DRAFT,
    MIN_GROUP,
    REVIEWED,
    Candidate,
    LabelFile,
    draft_label,
    guess_language,
    load_labels,
    near_duplicate_groups,
    pick_diverse,
    present_sections,
    save_label,
    similarity,
    validate,
)
from scripts import real_cv_prepare

SECRET = "Zaphod Beeblebrox"


def label(cv_id="cv-001", status=REVIEWED, **entities):
    base = {name: [] for name in FIELDS}
    base.update(entities)

    return LabelFile(
        id=cv_id,
        file=f"{cv_id}.pdf",
        status=status,
        tags={"language": "en", "layout": "single", "industry": "finance"},
        sections_present=["experience", "education"],
        entities=base,
    )


EXTRACTED = {
    "personal_info": {"full_name": SECRET},
    "experience": [{"company": "Acme Corp", "role": "Analyst"}],
    "education": [{"institution": "Hanoi University", "degree_level": ["BSc"]}],
    "skills": ["python"],
    "certifications": [],
}


# ------------------------------------------------------------- label files


def test_a_label_survives_saving_and_loading(tmp_path):
    original = label(name=[SECRET], companies=["Acme Corp"])
    save_label(tmp_path, original)

    loaded = load_labels(tmp_path)

    assert loaded == [original]


def test_the_index_and_the_pick_list_are_not_labels(tmp_path):
    save_label(tmp_path, label())
    (tmp_path / "index.json").write_text("{}", encoding="utf-8")
    (tmp_path / "picked.json").write_text("{}", encoding="utf-8")

    assert [item.id for item in load_labels(tmp_path)] == ["cv-001"]


def test_a_file_that_is_not_json_is_reported_not_crashed_on(tmp_path):
    (tmp_path / "cv-002.json").write_text("{oops", encoding="utf-8")

    assert validate(load_labels(tmp_path)) == ["cv-002: file is not valid JSON"]


def test_validation_finds_the_usual_mistakes():
    problems = validate(
        [
            LabelFile("cv-1", "a.pdf", "maybe"),
            LabelFile("cv-2", "", REVIEWED, entities={"companies": ["x"]}),
            LabelFile("cv-3", "a.pdf", REVIEWED, entities={"companies": ["x"]}),
            LabelFile("cv-4", "b.pdf", REVIEWED, sections_present=["hobbies"], entities={"pets": ["x"]}),
            LabelFile("cv-5", "c.pdf", REVIEWED),
        ]
    )

    text = "\n".join(problems)

    assert "cv-1: status must be" in text
    assert "cv-2: no PDF file name" in text
    assert "cv-3: same PDF as cv-1" in text
    assert "cv-4: unknown sections" in text and "cv-4: unknown entity fields" in text
    assert "cv-5: reviewed but has no entities" in text


def test_a_good_label_has_no_problems():
    assert validate([label(companies=["Acme"])]) == []


# --------------------------------------------------------------- drafting


def test_a_draft_is_made_from_the_extraction_and_is_not_reviewed():
    sections = {"experience": ["x"], "skills": ["  "], "__projects_regions__": ["y"]}

    draft = draft_label("cv-009", "cv.pdf", EXTRACTED, sections, {"language": "en"})

    assert draft.status == DRAFT
    assert draft.entities["companies"] == ["Acme Corp"]
    assert draft.sections_present == ["experience"]


@pytest.mark.parametrize(
    "text, expected",
    [
        ("Software engineer with experience in Python", "en"),
        ("Kỹ sư phần mềm có kinh nghiệm làm việc tại Hà Nội", "vi"),
        ("ソフトウェアエンジニア 東京", "other"),
        ("", "other"),
        ("12345 ---", "other"),
    ],
)
def test_language_guess(text, expected):
    assert guess_language(text) == expected


def test_present_sections_ignores_private_and_blank_sections():
    assert present_sections(
        {"education": ["a"], "summary": [" "], "personal_info": ["n"], "__x__": ["y"]}
    ) == ["education"]


# ---------------------------------------------------------------- picking


def candidate(name, text, pages=1, columns=1, language="en", chars=2000):
    return Candidate(name, pages, columns, language, chars, text)


TEMPLATE = "name role company skills python sql docker kubernetes aws gcp azure " * 5


def test_near_identical_texts_are_grouped():
    assert similarity(TEMPLATE, TEMPLATE + " one more") > 0.8
    assert similarity(TEMPLATE, "something entirely different about nursing wards") < 0.1
    assert similarity("", "x") == 0.0

    groups_found = near_duplicate_groups(
        [candidate("a", TEMPLATE), candidate("b", TEMPLATE + " x"), candidate("c", "nursing ward care plans for surgical patients every single day of the week")]
    )

    assert sorted(len(g) for g in groups_found) == [1, 2]


def test_a_template_used_many_times_is_capped():
    pool = [candidate(f"t{n}", TEMPLATE + f" {n}") for n in range(10)]
    pool.append(candidate("other", "a nursing cv about wards and patients and charts and care plans"))

    picked = pick_diverse(pool, count=20, per_template=2)

    assert len([c for c in picked if c.name.startswith("t")]) == 2
    assert "other" in {c.name for c in picked}


def test_picking_prefers_variety():
    pool = [
        candidate(f"en{n}", f"english cv number {n} " * 30 + str(n), columns=1)
        for n in range(6)
    ] + [
        candidate("vi", "kỹ sư phần mềm làm việc tại công ty " * 30, language="vi", columns=2, pages=3, chars=9000)
    ]

    picked = pick_diverse(pool, count=2)

    assert "vi" in {c.name for c in picked}
    assert len(picked) == 2


# ---------------------------------------------------------------- scoring


def test_an_unreviewed_label_cannot_be_scored():
    with pytest.raises(ValueError):
        score_cv(label(status=DRAFT, companies=["Acme"]), EXTRACTED, {})


def test_a_perfect_extraction_scores_one():
    truth = label(
        name=[SECRET],
        companies=["Acme Corp"],
        roles=["Analyst"],
        schools=["Hanoi University"],
        degrees=["BSc"],
    )

    result = score_cv(truth, EXTRACTED, {"experience": ["x"], "education": ["y"]})

    assert core_f1([result]) == pytest.approx(1.0)
    assert result.predicted_sections == ["experience", "education"]


def test_missing_and_invented_entities_lower_the_score():
    truth = label(companies=["Acme Corp", "Globex"], roles=["Analyst"])

    result = score_cv(truth, EXTRACTED, {})

    assert 0 < core_f1([result]) < 1


def test_the_interval_of_identical_cvs_is_a_point():
    results = [score_cv(label(f"cv-{n}", companies=["Acme Corp"]), EXTRACTED, {}) for n in range(5)]

    low, high = bootstrap_interval(results, core_f1)

    assert low == high == pytest.approx(core_f1(results))


def test_the_interval_contains_the_estimate_and_widens_with_variety():
    good = score_cv(label("cv-1", companies=["Acme Corp"]), EXTRACTED, {})
    bad = score_cv(label("cv-2", companies=["Nothing Like It"]), EXTRACTED, {})
    results = [good, bad] * 4

    low, high = bootstrap_interval(results, core_f1)

    assert low <= core_f1(results) <= high
    assert high > low


def test_section_presence_counts_found_and_real_sections():
    results = [
        CVResult("a", {}, {}, ["experience"], ["experience", "education"]),
        CVResult("b", {}, {}, ["experience", "skills"], ["experience"]),
    ]

    table = section_presence(results)

    assert table["experience"] == (1.0, 1.0, 2)
    assert table["education"] == (0.0, 0.0, 1)
    assert table["skills"] == (0.0, 0.0, 0)


def test_small_groups_are_merged_not_reported():
    def result(cv_id, language):
        return CVResult(cv_id, {"language": language}, {}, [], [])

    members = groups(
        [result("1", "en"), result("2", "en"), result("3", "en"), result("4", "vi"), result("5", "fr")],
        "language",
    )

    assert set(members) == {"en", f"other (fewer than {MIN_GROUP} each)"}
    assert len(members[f"other (fewer than {MIN_GROUP} each)"]) == 2


def test_the_weakest_cvs_are_listed_by_id():
    good = score_cv(label("cv-1", companies=["Acme Corp"]), EXTRACTED, {})
    bad = score_cv(label("cv-2", companies=["Elsewhere Inc"]), EXTRACTED, {})

    assert weakest([good, bad], limit=1)[0][0] == "cv-2"


def test_the_published_report_contains_no_personal_text():
    truth = [
        label(f"cv-{n}", name=[SECRET], companies=["Acme Corp"], roles=["Analyst"])
        for n in range(4)
    ]
    results = [score_cv(item, EXTRACTED, {"experience": ["x"]}, seconds=3.0) for item in truth]

    text = "\n".join(report(results, "Real CVs", "rules only"))

    assert SECRET not in text and "Acme" not in text and "Analyst" not in text
    assert ".pdf" not in text and "cv-0" not in text
    assert "Core entity F1" in text
    assert "## By language" in text
    for name in CORE_FIELDS:
        assert f"| {name} |" in text


def test_a_report_without_reviewed_cvs_says_so():
    assert "No reviewed CVs" in "\n".join(report([], "T", "m"))


# ----------------------------------------------------------- the commands


@pytest.fixture(scope="module")
def pdf_folder(tmp_path_factory):
    folder = tmp_path_factory.mktemp("cvs")
    IndustryCorpusBuilder(
        seed=1, industries=["finance"], layouts=["single", "two_column", "timeline"], wordings=("standard",)
    ).build(folder)

    return folder


def test_pick_saves_the_choice_and_prints_no_file_names(pdf_folder, tmp_path, capsys):
    real_cv_prepare.main(
        ["--labels", str(tmp_path), "pick", "--folder", str(pdf_folder), "--count", "3"]
    )

    printed = capsys.readouterr().out
    picked = json.loads((tmp_path / "picked.json").read_text(encoding="utf-8"))

    assert 1 <= len(picked["files"]) <= 3
    assert not any(name in printed for name in picked["files"])
    assert ".pdf" not in printed


def test_check_passes_for_good_labels_and_fails_for_bad_ones(tmp_path, capsys):
    save_label(tmp_path, label("cv-001", companies=["Acme"]))
    real_cv_prepare.main(["--labels", str(tmp_path), "check"])

    assert "No problems found" in capsys.readouterr().out

    save_label(tmp_path, LabelFile("cv-002", "", "nonsense"))

    with pytest.raises(SystemExit):
        real_cv_prepare.main(["--labels", str(tmp_path), "check"])


def test_mark_only_accepts_labels_that_pass_validation(tmp_path, capsys):
    save_label(tmp_path, label("cv-001", status=DRAFT, companies=["Acme"]))
    save_label(tmp_path, label("cv-002", status=DRAFT))

    real_cv_prepare.main(["--labels", str(tmp_path), "mark", "cv-001", "cv-002", "cv-003"])

    printed = capsys.readouterr().out
    saved = {item.id: item.status for item in load_labels(tmp_path)}

    assert saved == {"cv-001": REVIEWED, "cv-002": DRAFT}
    assert "cv-001: marked as reviewed" in printed
    assert "cv-002: reviewed but has no entities" in printed
    assert "cv-003: no such label" in printed


def test_mark_all_reviews_every_valid_draft(tmp_path):
    for number in (1, 2):
        save_label(tmp_path, label(f"cv-00{number}", status=DRAFT, companies=["Acme"]))

    real_cv_prepare.main(["--labels", str(tmp_path), "mark", "--all"])

    assert {item.status for item in load_labels(tmp_path)} == {REVIEWED}


def test_undefined_resamples_do_not_drag_the_interval_to_zero():
    # Only one of five CVs lists a company: resamples without it have no F1.
    results = [score_cv(label("cv-1", companies=["Acme Corp"]), EXTRACTED, {})]
    results += [score_cv(label(f"cv-{n}"), {}, {}) for n in range(2, 6)]

    from app.evaluation.real_cv_scoring import _field_f1

    low, high = bootstrap_interval(results, _field_f1("companies"))

    assert low == high == 1.0
