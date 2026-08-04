from app.repositories.skill_alias_repository import (
    SkillAliasRepository,
)


class FakeSkillAliasRepository(
    SkillAliasRepository
):

    def __init__(
        self,
        aliases
    ):
        self.aliases = aliases


    def get_alias(
        self,
        skill
    ):

        return self.aliases.get(skill)