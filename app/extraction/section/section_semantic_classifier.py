from __future__ import annotations

from typing import Dict, List, Tuple

import numpy as np
from loguru import logger
from sentence_transformers import util

from app.embeddings.models.embedding_model import (
    EmbeddingModelSingleton,
)


class SectionSemanticClassifier:

    SECTION_PROTOTYPES: Dict[str, List[str]] = {
        "personal_info": [
            (
                "Candidate identity and personal contact information "
                "including contact details, location, social links, "
                "and personal profile information."
            ),
            (
                "Information identifying the candidate and providing "
                "ways to contact or locate the person."
            ),
        ],
        "summary": [
            (
                "Professional profile, career objective, professional "
                "summary, introduction, career direction, or candidate "
                "overview."
            ),
            (
                "A concise professional introduction describing the "
                "candidate's background, goals, strengths, or direction."
            ),
        ],
        "education": [
            (
                "Formal academic background including educational "
                "institutions, degrees, academic programs, fields of "
                "study, and study periods."
            ),
            (
                "Academic history describing formal education and "
                "qualifications obtained through educational institutions."
            ),
        ],
        "experience": [
            (
                "Professional employment and work history including "
                "roles, internships, organizations, responsibilities, "
                "work periods, and professional achievements."
            ),
            (
                "Career history describing professional activities, "
                "employment, internships, responsibilities, and progression."
            ),
        ],
        "projects": [
            (
                "Projects, academic projects, personal projects, research "
                "work, portfolio work, technical projects, or project-based "
                "activities."
            ),
            (
                "Practical work carried out as a project, including its "
                "purpose, implementation, research, design, analysis, "
                "or delivered result."
            ),
        ],
        "certifications": [
            (
                "Professional certifications, certificates, licenses, "
                "credentials, accreditation, examinations, or formal "
                "qualifications."
            ),
            (
                "Recognized credentials demonstrating completion of a "
                "qualification, examination, training, or certification."
            ),
        ],
        "skills": [
            (
                "Skills, competencies, technical abilities, professional "
                "abilities, technologies, tools, methods, and areas of "
                "expertise."
            ),
            (
                "Capabilities, technologies, tools, knowledge areas, "
                "and professional competencies possessed by a candidate."
            ),
        ],
        "other": [
            (
                "Resume information that does not clearly belong to "
                "personal information, summary, education, experience, "
                "projects, certifications, or skills."
            ),
            (
                "Miscellaneous candidate information outside the main "
                "supported resume section categories."
            ),
        ],
    }

    BOUNDARY_PROTOTYPES: List[str] = [
        (
            "A standalone heading introducing a new major section "
            "of a professional resume or curriculum vitae."
        ),
        (
            "A concise heading marking the beginning of a new semantic "
            "region in a professional document."
        ),
        (
            "A section label separating one category of resume information "
            "from another."
        ),
    ]

    CONTENT_PROTOTYPES: List[str] = [
        (
            "A normal body-content line containing information belonging "
            "to an existing resume section."
        ),
        (
            "A detailed resume content line describing a person, activity, "
            "organization, project, qualification, responsibility, or skill."
        ),
        (
            "A body-content line providing details rather than starting "
            "a new semantic section."
        ),
    ]

    MIN_BOUNDARY_SCORE = 0.54
    MIN_SECTION_SCORE = 0.20
    MIN_SECTION_MARGIN = 0.025

    def __init__(self) -> None:

        logger.info(
            "Initializing fast semantic section classifier..."
        )

        embedding_singleton = EmbeddingModelSingleton()

        self.model = embedding_singleton.model

        self.section_types = list(
            self.SECTION_PROTOTYPES.keys()
        )

        self.prototype_texts: List[str] = []

        self.prototype_groups: Dict[str, List[int]] = {}

        for section_type in self.section_types:

            start_index = len(
                self.prototype_texts
            )

            descriptions = self.SECTION_PROTOTYPES[
                section_type
            ]

            self.prototype_texts.extend(
                descriptions
            )

            end_index = len(
                self.prototype_texts
            )

            self.prototype_groups[
                section_type
            ] = list(
                range(
                    start_index,
                    end_index,
                )
            )

        self.prototype_embeddings = self._encode(
            self.prototype_texts
        )

        self.boundary_embeddings = self._encode(
            self.BOUNDARY_PROTOTYPES
        )

        self.content_embeddings = self._encode(
            self.CONTENT_PROTOTYPES
        )

        logger.success(
            "Fast semantic section classifier initialized: "
            "{} section types, {} section prototypes",
            len(self.section_types),
            len(self.prototype_texts),
        )

    def classify(
        self,
        text: str,
    ) -> Tuple[str, float]:

        if not text or not text.strip():
            return "other", 0.0

        results = self.classify_batch(
            [text]
        )

        if not results:
            return "other", 0.0

        return results[0]

    def classify_batch(
        self,
        texts: List[str],
    ) -> List[Tuple[str, float]]:

        detailed = self.classify_detailed(
            texts
        )

        return [
            (
                str(item["section_type"]),
                float(item["confidence"]),
            )
            for item in detailed
        ]

    def classify_detailed(
        self,
        texts: List[str],
    ) -> List[Dict[str, object]]:

        normalized_texts = self._normalize_texts(
            texts
        )

        if not normalized_texts:
            return []

        embeddings = self._encode(
            normalized_texts
        )

        similarity = util.cos_sim(
            embeddings,
            self.prototype_embeddings,
        )

        scores = self._to_numpy(
            similarity
        )

        results: List[
            Dict[str, object]
        ] = []

        for text, row in zip(
            normalized_texts,
            scores,
        ):

            section_scores = (
                self._aggregate_section_scores(
                    row
                )
            )

            ordered_sections = sorted(
                section_scores.items(),
                key=lambda item: item[1],
                reverse=True,
            )

            best_section, best_score = (
                ordered_sections[0]
            )

            second_score = (
                ordered_sections[1][1]
                if len(ordered_sections) > 1
                else 0.0
            )

            confidence = (
                self._calculate_confidence(
                    best_score=best_score,
                    second_score=second_score,
                )
            )

            results.append(
                {
                    "text": text,
                    "section_type": best_section,
                    "score": float(best_score),
                    "confidence": float(confidence),
                    "margin": float(
                        best_score - second_score
                    ),
                    "ranking": [
                        {
                            "section_type": section_type,
                            "score": float(score),
                        }
                        for section_type, score
                        in ordered_sections
                    ],
                }
            )

        return results

    def classify_lines(
        self,
        lines: List[str],
    ) -> List[Dict[str, object]]:

        normalized_lines = self._normalize_texts(
            lines
        )

        if not normalized_lines:
            return []

        logger.info(
            "Running fast semantic section analysis for {} lines",
            len(normalized_lines),
        )

        line_embeddings = self._encode(
            normalized_lines
        )

        section_similarity = util.cos_sim(
            line_embeddings,
            self.prototype_embeddings,
        )

        boundary_similarity = util.cos_sim(
            line_embeddings,
            self.boundary_embeddings,
        )

        content_similarity = util.cos_sim(
            line_embeddings,
            self.content_embeddings,
        )

        section_array = self._to_numpy(
            section_similarity
        )

        boundary_array = self._to_numpy(
            boundary_similarity
        )

        content_array = self._to_numpy(
            content_similarity
        )

        line_count = len(
            normalized_lines
        )

        best_section_scores: List[float] = []

        for row in section_array:

            section_scores = (
                self._aggregate_section_scores(
                    row
                )
            )

            best_section_scores.append(
                max(
                    section_scores.values()
                )
            )

        results: List[
            Dict[str, object]
        ] = []

        for index, line in enumerate(
            normalized_lines
        ):

            section_scores = (
                self._aggregate_section_scores(
                    section_array[index]
                )
            )

            ordered_sections = sorted(
                section_scores.items(),
                key=lambda item: item[1],
                reverse=True,
            )

            best_section, best_section_score = (
                ordered_sections[0]
            )

            second_section_score = (
                ordered_sections[1][1]
                if len(ordered_sections) > 1
                else 0.0
            )

            section_margin = (
                best_section_score
                - second_section_score
            )

            boundary_score = float(
                np.max(
                    boundary_array[index]
                )
            )

            content_score = float(
                np.max(
                    content_array[index]
                )
            )

            boundary_signal = (
                boundary_score
                - content_score
            )

            semantic_strength = (
                self._normalize_similarity(
                    best_section_score
                )
            )

            boundary_strength = (
                self._normalize_similarity(
                    boundary_signal
                )
            )

            previous_score = (
                best_section_scores[index - 1]
                if index > 0
                else 0.0
            )

            next_score = (
                best_section_scores[index + 1]
                if index + 1 < line_count
                else 0.0
            )

            context_signal = (
                self._calculate_context_signal(
                    current_score=best_section_score,
                    previous_score=previous_score,
                    next_score=next_score,
                )
            )

            compactness = (
                self._calculate_compactness(
                    line
                )
            )

            final_boundary_score = (
                0.45 * boundary_strength
                + 0.25 * semantic_strength
                + 0.20 * context_signal
                + 0.10 * compactness
            )

            confidence = (
                self._calculate_boundary_confidence(
                    boundary_score=final_boundary_score,
                    section_margin=section_margin,
                    semantic_score=best_section_score,
                )
            )

            results.append(
                {
                    "line_index": index,
                    "text": line,
                    "section_type": best_section,
                    "section_score": float(
                        best_section_score
                    ),
                    "section_margin": float(
                        section_margin
                    ),
                    "boundary_score": float(
                        final_boundary_score
                    ),
                    "boundary_similarity": float(
                        boundary_score
                    ),
                    "content_similarity": float(
                        content_score
                    ),
                    "boundary_signal": float(
                        boundary_signal
                    ),
                    "context_signal": float(
                        context_signal
                    ),
                    "compactness": float(
                        compactness
                    ),
                    "confidence": float(
                        confidence
                    ),
                    "is_boundary": False,
                    "ranking": [
                        {
                            "section_type": section_type,
                            "score": float(score),
                        }
                        for section_type, score
                        in ordered_sections
                    ],
                }
            )

        results = self._resolve_boundary_candidates(
            results
        )

        boundary_count = sum(
            1
            for item in results
            if bool(
                item.get(
                    "is_boundary",
                    False,
                )
            )
        )

        logger.info(
            "Fast semantic analysis produced {} "
            "candidate boundaries",
            boundary_count,
        )

        return results

    def _resolve_boundary_candidates(
        self,
        results: List[Dict[str, object]],
    ) -> List[Dict[str, object]]:

        if not results:
            return []

        candidate_indices = [
            index
            for index, item in enumerate(results)
            if float(
                item.get(
                    "boundary_score",
                    0.0,
                )
            ) >= self.MIN_BOUNDARY_SCORE
        ]

        if not candidate_indices:
            return results

        for index in candidate_indices:

            item = results[index]

            score = float(
                item.get(
                    "boundary_score",
                    0.0,
                )
            )

            previous_score = (
                float(
                    results[index - 1].get(
                        "boundary_score",
                        0.0,
                    )
                )
                if index > 0
                else -1.0
            )

            next_score = (
                float(
                    results[index + 1].get(
                        "boundary_score",
                        0.0,
                    )
                )
                if index + 1 < len(results)
                else -1.0
            )

            if score < previous_score:
                continue

            if score < next_score:
                continue

            semantic_score = float(
                item.get(
                    "section_score",
                    0.0,
                )
            )

            if semantic_score < self.MIN_SECTION_SCORE:
                continue

            section_margin = float(
                item.get(
                    "section_margin",
                    0.0,
                )
            )

            if section_margin < self.MIN_SECTION_MARGIN:
                continue

            item["is_boundary"] = True

        boundary_indices = [
            index
            for index, item in enumerate(results)
            if bool(
                item.get(
                    "is_boundary",
                    False,
                )
            )
        ]

        for left, right in zip(
            boundary_indices,
            boundary_indices[1:],
        ):

            if right - left != 1:
                continue

            left_score = float(
                results[left].get(
                    "boundary_score",
                    0.0,
                )
            )

            right_score = float(
                results[right].get(
                    "boundary_score",
                    0.0,
                )
            )

            if left_score >= right_score:
                results[right][
                    "is_boundary"
                ] = False
            else:
                results[left][
                    "is_boundary"
                ] = False

        return results

    @staticmethod
    def _encode(
        texts: List[str],
    ):

        return EmbeddingModelSingleton().model.encode(
            texts,
            convert_to_tensor=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )

    @staticmethod
    def _to_numpy(
        tensor,
    ) -> np.ndarray:

        return (
            tensor
            .detach()
            .cpu()
            .numpy()
        )

    @staticmethod
    def _normalize_texts(
        texts: List[str],
    ) -> List[str]:

        return [
            text.strip()
            for text in texts
            if isinstance(text, str)
            and text.strip()
        ]

    def _aggregate_section_scores(
        self,
        prototype_scores: np.ndarray,
    ) -> Dict[str, float]:

        section_scores: Dict[str, float] = {}

        for section_type, indices in (
            self.prototype_groups.items()
        ):

            values = [
                float(
                    prototype_scores[index]
                )
                for index in indices
            ]

            section_scores[
                section_type
            ] = (
                max(values)
                if values
                else 0.0
            )

        return section_scores

    @staticmethod
    def _normalize_similarity(
        value: float,
    ) -> float:

        return max(
            0.0,
            min(
                1.0,
                (value + 1.0) / 2.0,
            ),
        )

    @staticmethod
    def _calculate_context_signal(
        current_score: float,
        previous_score: float,
        next_score: float,
    ) -> float:

        surrounding = (
            previous_score
            + next_score
        ) / 2.0

        difference = (
            current_score
            - surrounding
        )

        return max(
            0.0,
            min(
                1.0,
                0.5 + difference,
            ),
        )

    @staticmethod
    def _calculate_compactness(
        text: str,
    ) -> float:

        words = text.split()

        if not words:
            return 0.0

        word_count = len(words)

        if word_count <= 2:
            return 1.0

        if word_count <= 4:
            return 0.85

        if word_count <= 7:
            return 0.60

        if word_count <= 10:
            return 0.35

        return 0.10

    @staticmethod
    def _calculate_boundary_confidence(
        boundary_score: float,
        section_margin: float,
        semantic_score: float,
    ) -> float:

        margin_component = max(
            0.0,
            min(
                1.0,
                section_margin * 4.0,
            ),
        )

        semantic_component = (
            SectionSemanticClassifier._normalize_similarity(
                semantic_score
            )
        )

        confidence = (
            0.60 * boundary_score
            + 0.25 * margin_component
            + 0.15 * semantic_component
        )

        return max(
            0.0,
            min(
                1.0,
                confidence,
            )
        )

    @staticmethod
    def _calculate_confidence(
        best_score: float,
        second_score: float,
    ) -> float:

        margin = max(
            0.0,
            best_score - second_score,
        )

        similarity_component = max(
            0.0,
            min(
                1.0,
                (best_score + 1.0) / 2.0,
            ),
        )

        margin_component = max(
            0.0,
            min(
                1.0,
                margin * 5.0,
            ),
        )

        confidence = (
            0.65 * similarity_component
            + 0.35 * margin_component
        )

        return max(
            0.0,
            min(
                1.0,
                confidence,
            ),
        )