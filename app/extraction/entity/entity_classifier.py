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

        # Taxonomy evidence has priority for known skills.
        if self._is_known_skill(text):
            return EntityType.SKILL

        # NER evidence.
        if ner_label == "PERSON":
            return EntityType.PERSON

        if ner_label == "ORG":
            return EntityType.COMPANY

        # Contextual evidence.
        contextual_type = self._classify_from_context(
            text=text,
            context=context,
        )

        if contextual_type != EntityType.UNKNOWN:
            return contextual_type

        return EntityType.UNKNOWN


    def _is_known_skill(self, text: str) -> bool:

        skill = self.skill_repository.find(text)

        return skill is not None

    def _classify_from_context(
        self,
        text: str,
        context: str | None,
    ) -> EntityType:

        if not context:
            return EntityType.UNKNOWN

        return EntityType.UNKNOWN