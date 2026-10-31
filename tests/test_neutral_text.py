import pytest

from app.matching import embedding_text
from app.matching.embedding_text import CandidateTextBuilder
from app.matching.neutral_text import neutralise
from app.models.candidate import CandidateModel, Experience


@pytest.mark.parametrize(
    "text, expected",
    [
        ("She leads the team.", "they leads the team."),
        ("He enjoys mentoring his colleagues.", "they enjoys mentoring their colleagues."),
        ("Her work helped him.", "their work helped them."),
        ("Mr. Smith built it.", "Smith built it."),
        ("Anh ấy làm việc với Python.", "họ làm việc với Python."),
    ],
)
def test_gendered_words_are_replaced(text, expected):
    assert neutralise(text) == expected


def test_words_that_only_contain_a_pronoun_are_left_alone():
    text = "Used SHE metrics with Shell scripts, then the helpers and other tools."

    assert neutralise(text) == text


def test_the_persons_name_and_its_parts_are_removed():
    text = "Nguyen Van An is a backend engineer. An built payment services."

    cleaned = neutralise(text, "Nguyen Van An")

    assert "Nguyen" not in cleaned and "Van" not in cleaned
    assert "backend engineer" in cleaned and "payment services" in cleaned


def test_short_name_parts_are_not_removed_as_words():
    # "An" has two letters: removing it would also damage ordinary words.
    assert "an" in neutralise("Wrote an API for the team", "Le An")


def test_empty_input_is_returned_as_it_is():
    assert neutralise("") == ""
    assert neutralise("plain text", None) == "plain text"


def candidate(**fields):
    return CandidateModel(
        resume_id="r",
        faiss_id=1,
        skills=["python"],
        experience=[
            Experience(role="Engineer", company="Acme", description=["She built services in Python."])
        ],
        **fields,
    )


def test_the_embedding_text_has_no_pronouns_or_name():
    profile = candidate(
        summary="Zxqv Unique is an engineer. She likes data.",
        personal_info={"full_name": "Zxqv Unique"},
    )

    text = CandidateTextBuilder().text(profile)

    assert "Zxqv" not in text
    assert "She" not in text and "they" in text
    assert "python" in text.lower()


def test_two_profiles_that_differ_only_by_pronoun_get_the_same_text():
    she = candidate(summary="Engineer. She enjoys mentoring.")
    he = candidate(summary="Engineer. He enjoys mentoring.")
    builder = CandidateTextBuilder()

    assert builder.text(she) == builder.text(he)


def test_the_switch_restores_the_text_as_written(monkeypatch):
    monkeypatch.setattr(embedding_text, "NEUTRALISE_TEXT", False)
    profile = candidate(summary="Engineer. She enjoys mentoring.")

    assert "She enjoys" in CandidateTextBuilder().text(profile)


def test_the_embedding_version_changed_with_the_text():
    from app.core.constants.app_constants import EMBEDDING_VERSION

    assert EMBEDDING_VERSION != "profile-v1"
