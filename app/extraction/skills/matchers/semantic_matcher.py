from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from app.extraction.skills.repository import SkillRepository

import numpy as np


class SemanticSkillMatcher:

    def __init__(self):
        self.repository = SkillRepository()
        self.skill_objects = (
            self.repository.get_all_skill_objects()
        )
        self.model = SentenceTransformer(
            "all-MiniLM-L6-v2"
        )
        self.corpus = [
            self._build_document(skill)
            for skill in self.skill_objects
        ]
        self.skill_embeddings = self.model.encode(
            self.corpus,
            convert_to_numpy=True,
            show_progress_bar=True
        )
        
        
    def find_best_match(
        self,
        query: str,
        threshold: float = 0.60
    ):

        query_embedding = self.model.encode(
            [query],
            convert_to_numpy=True
        )

        similarities = cosine_similarity(
            query_embedding,
            self.skill_embeddings
        )[0]

        best_index = np.argmax(
            similarities
        )

        score = similarities[
            best_index
        ]

        if score < threshold:
            return None

        best_skill = self.skill_objects[
            best_index
        ]

        return (
            best_skill["name"],
            float(score)
        )
        
    def match(
        self,
        text: str,
        threshold: float = 0.70
    ):
        extracted = set()

        words = text.split()

        for word in words:

            result = self.find_best_match(
                word,
                threshold
            )

            if result:
                skill, _ = result
                extracted.add(skill)

        return extracted
        
    def _build_document(self, skill):
        parts = [
            skill["name"],
            skill.get("domain", ""),
            skill.get("category", "")
        ]

        parts.extend(
            skill.get("aliases", [])
        )

        return " ".join(
            part
            for part in parts
            if part
        )