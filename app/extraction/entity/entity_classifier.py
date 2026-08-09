from typing import Dict

from app.extraction.entity.entity_types import EntityType
from app.extraction.skills.repository import SkillRepository


class EntityClassifier:

    def __init__(self):
        self.skill_repository = SkillRepository()

    def classify(
        self,
        text: str,
        context: str | None = None,
        ner_label: str | None = None,
    ) -> Dict:

        entity_type = self._classify(
            text=text,
            context=context,
            ner_label=ner_label,
        )

        return {
            "text": text,
            "type": entity_type,
        }

    def _classify(
        self,
        text: str,
        context: str | None,
        ner_label: str | None,
    ) -> EntityType:

        text = text.strip()

        if not text:
            return EntityType.UNKNOWN

        # Strong domain evidence.
        if self._is_known_skill(text):
            return EntityType.SKILL

        # NER is only evidence.
        entity_type = self._map_ner_label(ner_label)

        if entity_type is not EntityType.UNKNOWN:
            return entity_type

        return EntityType.UNKNOWN

    def _is_known_skill(
        self,
        text: str,
    ) -> bool:

        skill = self.skill_repository.find(text)

        return skill is not None

    @staticmethod
    def _map_ner_label(
        ner_label: str | None,
    ) -> EntityType:

        if not ner_label:
            return EntityType.UNKNOWN

        mapping = {
            "PERSON": EntityType.PERSON,
            "ORG": EntityType.COMPANY,
        }

        return mapping.get(
            ner_label,
            EntityType.UNKNOWN,
        )