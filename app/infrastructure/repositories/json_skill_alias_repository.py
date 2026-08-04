import json

from app.repositories.skill_alias_repository import (
    SkillAliasRepository,
)


class JsonSkillAliasRepository(
    SkillAliasRepository
):

    def __init__(
        self,
        file_path: str
    ):
        self.file_path = file_path

        with open(
            file_path,
            encoding="utf-8"
        ) as file:
            self.aliases = json.load(file)


    def get_alias(
        self,
        skill: str
    ) -> str | None:

        return self.aliases.get(skill)