from app.extraction.skills.repository import SkillRepository


def test_skill_repository():

    repo = SkillRepository()

    skills = repo.get_all_skills()

    print(skills)

    assert "Python" in skills
    assert "Machine Learning" in skills