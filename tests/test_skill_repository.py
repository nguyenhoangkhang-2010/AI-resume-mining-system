from app.extraction.skills.repository import SkillRepository
import inspect


def test_skill_repository():

    print("\nFILE:")
    print(inspect.getfile(SkillRepository))

    print("\nMETHOD:")
    print(
        inspect.getsource(
            SkillRepository.get_all_skills
        )
    )

    repo = SkillRepository()

    skills = repo.get_all_skills()

    print("\nSKILLS:")
    print(skills)

    assert "Python" in skills