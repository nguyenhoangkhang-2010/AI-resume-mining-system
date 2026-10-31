from app.extraction.rules import stats
from app.schemas.resume_schema import ConfidenceInfo
from app.services.confidence import HIGH, LOW, assess_confidence, level_of

LONG_TEXT = "x" * 2000


def good_cv(**overrides):
    cv = {
        "raw_text": LONG_TEXT,
        "personal_info": {"full_name": "A B", "email": "a@b.co"},
        "experience": [
            {
                "company": "Acme",
                "role": "Engineer",
                "start_date": "2020-01",
                "end_date": "2022-01",
            }
        ],
        "education": [{"institution": "State University", "degree": "BSc"}],
        "skills": ["python"],
        "signals": {
            "sections": [
                "personal_info:contact_header:1.00",
                "experience:heading_words:1.00",
                "education:heading_words:1.00",
                "skills:heading_words:1.00",
            ],
            "methods": {"experience.rules": 2, "education.rules": 1},
            "pages": 1,
            "ocr_pages": 0,
        },
    }
    cv.update(overrides)

    return cv


def test_clean_cv_is_high_confidence():
    result = assess_confidence(good_cv())

    assert result.level == HIGH
    assert result.score > 0.9
    assert result.reasons == []


def test_empty_result_is_low_confidence():
    result = assess_confidence({"raw_text": ""})

    assert result.level == LOW
    assert result.score < 0.1
    assert "experience_missing" in result.reasons


def test_sections_guessed_by_a_model_lower_the_score():
    guessed = good_cv()
    guessed["signals"] = {
        **guessed["signals"],
        "sections": [
            "experience:model_guess:0.50",
            "education:model_guess:0.50",
        ],
    }

    assert assess_confidence(guessed).score < assess_confidence(good_cv()).score
    assert "experience_section_guessed" in assess_confidence(guessed).reasons


def test_answers_from_the_model_lower_the_score_less_than_guessed_sections():
    by_model = good_cv()
    by_model["signals"] = {
        **by_model["signals"],
        "methods": {"experience.model": 1, "education.model": 1},
    }

    result = assess_confidence(by_model)

    assert result.score < assess_confidence(good_cv()).score
    assert result.level != LOW
    assert "experience_read_by_model" in result.reasons


def test_ocr_lowers_the_score_and_says_why():
    scanned = good_cv()
    scanned["signals"] = {**scanned["signals"], "ocr_pages": 1}

    result = assess_confidence(scanned)

    assert result.score < assess_confidence(good_cv()).score
    assert "read_by_ocr" in result.reasons


def test_entries_without_dates_are_reported():
    undated = good_cv(
        experience=[{"company": "Acme", "role": "Engineer"}],
    )

    result = assess_confidence(undated)

    assert "experience_without_dates" in result.reasons
    assert result.components["fields"] < 1.0


def test_result_without_signals_still_scores():
    cv = good_cv()
    del cv["signals"]

    result = assess_confidence(cv)

    assert 0.0 <= result.score <= 1.0


def test_score_stays_between_zero_and_one():
    for cv in (good_cv(), {"raw_text": ""}, good_cv(experience=[], skills=[])):
        assert 0.0 <= assess_confidence(cv).score <= 1.0


def test_levels_follow_the_thresholds():
    assert level_of(0.9) == "high"
    assert level_of(0.89) == "medium"
    assert level_of(0.5) == "medium"
    assert level_of(0.49) == "low"


def test_confidence_serialises_into_the_api_model():
    stored = assess_confidence(good_cv()).to_dict()

    info = ConfidenceInfo.from_document({"confidence": stored})

    assert info is not None
    assert info.level == "high"


def test_missing_or_broken_stored_confidence_is_none():
    assert ConfidenceInfo.from_document({}) is None
    assert ConfidenceInfo.from_document({"confidence": {"score": "bad"}}) is None


def test_document_counts_are_kept_apart_from_the_totals():
    stats.reset()
    stats.record("experience", True)

    token = stats.begin_document()
    stats.record("experience", False)
    stats.record("education", True)
    document = stats.end_document(token)

    stats.record("experience", True)

    assert document == {"experience.model": 1, "education.rules": 1}
    assert stats.snapshot()["experience.rules"] == 2
    assert stats.snapshot()["experience.model"] == 1

    stats.reset()


def test_nothing_is_counted_for_a_document_after_it_ends():
    token = stats.begin_document()
    stats.end_document(token)

    stats.record("skills", True)

    token = stats.begin_document()

    assert stats.end_document(token) == {}

    stats.reset()


def test_a_sentence_read_as_a_job_title_lowers_the_fields_score():
    sentence = "Responsible for building and maintaining many payment services for banks and shops"
    wrong = good_cv(
        experience=[
            {"company": "Acme", "role": sentence, "start_date": "2020", "end_date": "2021"}
        ]
    )

    assert (
        assess_confidence(wrong).components["fields"]
        < assess_confidence(good_cv()).components["fields"]
    )


def test_a_year_inside_a_company_name_is_not_plausible():
    wrong = good_cv(
        experience=[
            {"company": "Acme 2019 2021", "role": "Engineer", "start_date": "2020", "end_date": "2021"}
        ]
    )

    assert (
        assess_confidence(wrong).components["fields"]
        < assess_confidence(good_cv()).components["fields"]
    )


def test_dates_in_the_cv_that_no_entry_has_lower_the_score():
    text = "\n".join(
        ["Jan 2015 - Dec 2016", "Jan 2017 - Dec 2018", "Jan 2019 - Dec 2020", "Jan 2021 - Present"]
        + ["filler line"] * 80
    )
    lost_jobs = good_cv(raw_text=text, education=[])

    result = assess_confidence(lost_jobs)

    assert "dates_not_matched_to_entries" in result.reasons
    assert result.components["fields"] < 1.0


def test_every_date_range_matched_to_an_entry_is_fine():
    text = "\n".join(["Jan 2020 - Dec 2021"] * 1 + ["filler line"] * 80)

    assert "dates_not_matched_to_entries" not in assess_confidence(good_cv(raw_text=text)).reasons
