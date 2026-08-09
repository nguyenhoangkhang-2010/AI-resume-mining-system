from typing import Dict, List

from loguru import logger
from transformers import (
    AutoModelForTokenClassification,
    AutoTokenizer,
    pipeline,
)

from app.core.config.settings import settings


class NERService:

    def __init__(
        self,
        primary_model_name: str | None = None,
        multilingual_model_name: str | None = None,
    ):
        self.primary_model_name = (
            primary_model_name
            or settings.NER_PRIMARY_MODEL
        )

        self.multilingual_model_name = (
            multilingual_model_name
            or settings.NER_MULTILINGUAL_MODEL
        )

        self.confidence_threshold = (
            settings.NER_CONFIDENCE_THRESHOLD
        )

        self.primary_pipeline = None
        self.multilingual_pipeline = None

        if settings.NER_PRIMARY_ENABLED:
            self.primary_pipeline = self._load_pipeline(
                self.primary_model_name
            )

        if settings.NER_MULTILINGUAL_ENABLED:
            self.multilingual_pipeline = self._load_pipeline(
                self.multilingual_model_name
            )

        logger.info("NERService initialized.")

    def _load_pipeline(
        self,
        model_name: str,
    ):
        logger.info(
            f"Loading NER model: {model_name}"
        )

        tokenizer = AutoTokenizer.from_pretrained(
            model_name
        )

        model = AutoModelForTokenClassification.from_pretrained(
            model_name
        )

        return pipeline(
            "token-classification",
            model=model,
            tokenizer=tokenizer,
            aggregation_strategy="simple",
        )

    def extract(
        self,
        text: str,
        *,
        use_primary_model: bool = True,
        use_multilingual_model: bool = True,
    ) -> List[Dict]:

        if not text or not text.strip():
            return []

        results: List[Dict] = []

        if (
            use_primary_model
            and self.primary_pipeline is not None
        ):
            results.extend(
                self._extract_with_model(
                    text=text,
                    ner_pipeline=self.primary_pipeline,
                    source="primary",
                )
            )

        if (
            use_multilingual_model
            and self.multilingual_pipeline is not None
        ):
            results.extend(
                self._extract_with_model(
                    text=text,
                    ner_pipeline=self.multilingual_pipeline,
                    source="multilingual",
                )
            )

        self._current_text = text

        merged = self._merge_results(
            results,
            text,
        )

        refined = self._refine_entities(
            merged,
            text,
        )

        return self._reconstruct_entities(
            refined,
            text,
        )

    def _extract_with_model(
        self,
        text: str,
        ner_pipeline,
        source: str,
    ) -> List[Dict]:

        raw_entities = ner_pipeline(text)

        entities: List[Dict] = []

        for entity in raw_entities:
            score = float(entity["score"])

            if score < self.confidence_threshold:
                continue

            entity_text = entity["word"].strip()

            if not entity_text:
                continue

            raw_label = (
                entity.get("entity_group")
                or entity.get("entity")
            )

            label = self._normalize_label(
                raw_label,
                source=source,
            )

            candidate = {
                "text": entity_text,
                "label": label,
                "raw_label": raw_label,
                "score": score,
                "start": int(entity["start"]),
                "end": int(entity["end"]),
                "source": source,
            }

            if self._is_invalid_entity_text(candidate):
                logger.debug(
                    "Ignoring invalid NER entity: "
                    f"{candidate['text']!r} "
                    f"({candidate['label']})"
                )
                continue

            entities.append(candidate)

        return entities

    def _normalize_label(
        self,
        label: str | None,
        *,
        source: str,
    ) -> str:

        if not label:
            return "UNKNOWN"

        normalized = label.upper().strip()

        if normalized.startswith("B-") or normalized.startswith("I-"):
            normalized = normalized[2:]

        if source == "primary":
            mapping = {
                "NAME": "PERSON",
                "EMAIL": "EMAIL",
                "PHONE": "PHONE",
                "LOCATION": "LOC",
                "LOC": "LOC",
                "COMPANY": "ORG",
                "ORG": "ORG",
                "TITLE": "TITLE",
                "DATE": "DATE",
                "DEGREE": "DEGREE",
                "FIELD": "FIELD",
                "INSTITUTION": "INSTITUTION",
                "SKILL": "SKILL",
                "CERT": "CERTIFICATION",
                "CERTIFICATION": "CERTIFICATION",
                "LANGUAGE": "LANGUAGE",
            }

            return mapping.get(
                normalized,
                normalized,
            )

        if source == "multilingual":
            mapping = {
                "PER": "PERSON",
                "PERSON": "PERSON",
                "ORG": "ORG",
                "LOC": "LOC",
                "MISC": "MISC",
            }

            return mapping.get(
                normalized,
                normalized,
            )

        return normalized

    @staticmethod
    def _overlap(
        first: Dict,
        second: Dict,
    ) -> bool:

        return (
            first["start"] < second["end"]
            and second["start"] < first["end"]
        )
        
    @staticmethod
    def _entity_quality_score(
        entity: Dict,
    ) -> float:

        score = float(
            entity.get("score", 0.0)
        )

        text = str(
            entity.get("text", "")
        ).strip()

        if not text:
            return 0.0

        tokens = text.split()

        token_count = len(tokens)
        char_count = len(text)

        length_factor = min(
            1.0,
            char_count / 8.0,
        )

        token_factor = min(
            1.0,
            token_count / 2.0,
        )

        agreement = int(
            entity.get(
                "model_agreement",
                1,
            )
        )

        agreement_factor = min(
            1.0,
            agreement / 2.0,
        )

        return (
            score * 0.60
            + length_factor * 0.15
            + token_factor * 0.10
            + agreement_factor * 0.15
        )
        
    def _debug_model_outputs(
        self,
        text: str,
    ) -> None:

        if self.primary_pipeline is not None:
            primary = self._extract_with_model(
                text=text,
                ner_pipeline=self.primary_pipeline,
                source="primary",
            )

            logger.info(
                f"PRIMARY NER: {primary}"
            )

        if self.multilingual_pipeline is not None:
            multilingual = self._extract_with_model(
                text=text,
                ner_pipeline=self.multilingual_pipeline,
                source="multilingual",
            )

            logger.info(
                f"MULTILINGUAL NER: {multilingual}"
            )
        
    def _merge_results(
        self,
        entities: List[Dict],
        text: str,
    ) -> List[Dict]:

        if not entities:
            return []

        entities = self._filter_invalid_spans(
            entities,
            text,
        )
        
        entities = [
            entity
            for entity in entities
            if not self._is_invalid_entity_text(entity)
        ]

        candidates = [
            entity
            for entity in entities
            if (
                not self._is_invalid_entity_text(entity)
                and entity.get("start") is not None
                and entity.get("end") is not None
                and entity["end"] > entity["start"]
            )
        ]

        if not candidates:
            return []

        candidates.sort(
            key=lambda item: (
                item["start"],
                -(item["end"] - item["start"]),
                -float(item.get("score", 0.0)),
            )
        )

        selected: List[Dict] = []

        for candidate in candidates:
            conflicts = [
                existing
                for existing in selected
                if self._overlap(candidate, existing)
            ]
            
            if conflicts:
                preserve_nested = False

                for existing in conflicts:
                    candidate_start = int(candidate["start"])
                    candidate_end = int(candidate["end"])
                    existing_start = int(existing["start"])
                    existing_end = int(existing["end"])

                    candidate_contains_existing = (
                        candidate_start <= existing_start
                        and candidate_end >= existing_end
                    )

                    existing_contains_candidate = (
                        existing_start <= candidate_start
                        and existing_end >= candidate_end
                    )

                    different_labels = (
                        candidate.get("label")
                        != existing.get("label")
                    )

                    different_sources = (
                        candidate.get("source")
                        != existing.get("source")
                    )

                    if (
                        different_labels
                        and different_sources
                        and (
                            candidate_contains_existing
                            or existing_contains_candidate
                        )
                    ):
                        preserve_nested = True
                        break

                if preserve_nested:
                    selected.append(candidate)
                    continue

            if not conflicts:
                selected.append(candidate)
                continue

            keep_candidate = True

            replaced_existing = False

            for existing in conflicts:
                decision = self._compare_entities(
                    candidate,
                    existing,
                )

                if decision == "existing":
                    keep_candidate = False
                    break

                if decision == "candidate":
                    if existing in selected:
                        selected.remove(existing)
                        replaced_existing = True

            if keep_candidate:
                selected.append(candidate)

            if replaced_existing:
                selected.sort(
                    key=lambda item: (
                        item["start"],
                        item["end"],
                    )
                )

        return sorted(
            selected,
            key=lambda item: (
                item["start"],
                item["end"],
            ),
        )
        
    def _filter_invalid_spans(
        self,
        entities: List[Dict],
        text: str,
    ) -> List[Dict]:

        if not entities:
            return []

        filtered: List[Dict] = []

        for entity in entities:
            start = int(entity["start"])
            end = int(entity["end"])

            if end <= start:
                continue

            entity_text = text[start:end]

            newline_count = entity_text.count("\n")

            if newline_count >= 2:
                logger.debug(
                    "Ignoring suspicious multi-line NER span: "
                    f"{entity_text!r}"
                )
                continue

            filtered.append(entity)

        return filtered

    @staticmethod
    def _label_priority(
        label: str | None,
        source: str,
    ) -> float:

        if not label:
            return 0.0

        label = label.upper()

        if source == "primary":
            priorities = {
                "PERSON": 1.00,
                "EMAIL": 1.00,
                "PHONE": 1.00,
                "DEGREE": 1.00,
                "FIELD": 1.00,
                "SKILL": 1.00,
                "CERTIFICATION": 1.00,
                "LANGUAGE": 1.00,
                "INSTITUTION": 0.95,
                "ORG": 0.90,
                "LOC": 0.90,
                "TITLE": 0.95,
                "DATE": 0.95,
            }

        else:
            priorities = {
                "PERSON": 0.90,
                "ORG": 0.95,
                "LOC": 0.95,
                "MISC": 0.50,
            }

        return priorities.get(label, 0.50)

    def _compare_entities(
        self,
        candidate: Dict,
        existing: Dict,
    ) -> str:

        candidate_start = int(candidate["start"])
        candidate_end = int(candidate["end"])

        existing_start = int(existing["start"])
        existing_end = int(existing["end"])

        candidate_score = float(
            candidate.get("score", 0.0)
        )

        existing_score = float(
            existing.get("score", 0.0)
        )

        candidate_label = candidate.get("label")
        existing_label = existing.get("label")

        same_span = (
            candidate_start == existing_start
            and candidate_end == existing_end
        )

        if same_span and candidate_label == existing_label:

            candidate["model_agreement"] = (
                int(
                    existing.get(
                        "model_agreement",
                        1,
                    )
                ) + 1
            )

            candidate["score"] = max(
                candidate_score,
                existing_score,
            )

            candidate["source"] = "ensemble"

            return "candidate"

        if same_span and candidate_label != existing_label:

            candidate_priority = self._label_priority(
                candidate_label,
                candidate.get("source", ""),
            )

            existing_priority = self._label_priority(
                existing_label,
                existing.get("source", ""),
            )

            candidate_evidence = (
                candidate_score
                * candidate_priority
            )

            existing_evidence = (
                existing_score
                * existing_priority
            )

            candidate["label_candidates"] = list(
                dict.fromkeys(
                    [
                        candidate_label,
                        existing_label,
                    ]
                )
            )

            existing["label_candidates"] = list(
                dict.fromkeys(
                    [
                        existing_label,
                        candidate_label,
                    ]
                )
            )

            if candidate_evidence > existing_evidence:

                candidate["source"] = "ensemble"

                candidate["model_agreement"] = 1

                return "candidate"

            if existing_evidence > candidate_evidence:

                existing["source"] = "ensemble"

                existing["model_agreement"] = 1

                return "existing"

            if candidate_score >= existing_score:

                candidate["source"] = "ensemble"

                candidate["model_agreement"] = 1

                return "candidate"

            existing["source"] = "ensemble"

            existing["model_agreement"] = 1

            return "existing"

        overlap_start = max(
            candidate_start,
            existing_start,
        )

        overlap_end = min(
            candidate_end,
            existing_end,
        )

        overlap_length = max(
            0,
            overlap_end - overlap_start,
        )

        if overlap_length <= 0:
            return "candidate"

        candidate_length = max(
            1,
            candidate_end - candidate_start,
        )

        existing_length = max(
            1,
            existing_end - existing_start,
        )

        candidate_overlap_ratio = (
            overlap_length / candidate_length
        )

        existing_overlap_ratio = (
            overlap_length / existing_length
        )

        if candidate_label == existing_label:

            candidate_contains_existing = (
                candidate_start <= existing_start
                and candidate_end >= existing_end
            )

            existing_contains_candidate = (
                existing_start <= candidate_start
                and existing_end >= candidate_end
            )

            if candidate_label == existing_label:

                candidate_length = (
                    candidate_end - candidate_start
                )

                existing_length = (
                    existing_end - existing_start
                )

                if (
                    candidate_start == existing_start
                    and candidate_end == existing_end
                ):

                    candidate["model_agreement"] = (
                        int(
                            existing.get(
                                "model_agreement",
                                1,
                            )
                        ) + 1
                    )

                    if candidate_score >= existing_score:
                        candidate["source"] = "ensemble"
                        candidate["score"] = candidate_score

                        return "candidate"

                    existing["source"] = "ensemble"
                    existing["score"] = existing_score
                    existing["model_agreement"] = (
                        int(
                            existing.get(
                                "model_agreement",
                                1,
                            )
                        ) + 1
                    )

                    return "existing"

                candidate_contains_existing = (
                    candidate_start <= existing_start
                    and candidate_end >= existing_end
                )

                existing_contains_candidate = (
                    existing_start <= candidate_start
                    and existing_end >= candidate_end
                )

                if candidate_contains_existing:

                    if candidate_length > existing_length:
                        return "candidate"

                if existing_contains_candidate:

                    if existing_length > candidate_length:
                        return "existing"

                candidate_quality = (
                    self._entity_quality_score(candidate)
                )

                existing_quality = (
                    self._entity_quality_score(existing)
                )

                candidate_evidence = (
                    candidate_quality
                    * candidate_score
                )

                existing_evidence = (
                    existing_quality
                    * existing_score
                )

                if candidate_evidence > existing_evidence:
                    return "candidate"

                if existing_evidence > candidate_evidence:
                    return "existing"

                if candidate_score > existing_score:
                    return "candidate"

                if existing_score > candidate_score:
                    return "existing"

                if candidate_length > existing_length:
                    return "candidate"

                return "existing"

            if candidate_score > existing_score:
                return "candidate"

            if existing_score > candidate_score:
                return "existing"

            candidate_length = (
                candidate_end - candidate_start
            )

            existing_length = (
                existing_end - existing_start
            )

            if candidate_length > existing_length:
                return "candidate"

            return "existing"

        candidate_priority = self._label_priority(
            candidate_label,
            candidate.get("source", ""),
        )

        existing_priority = self._label_priority(
            existing_label,
            existing.get("source", ""),
        )

        candidate_evidence = (
            candidate_score
            * candidate_priority
            * candidate_overlap_ratio
        )

        existing_evidence = (
            existing_score
            * existing_priority
            * existing_overlap_ratio
        )

        candidate["label_candidates"] = list(
            dict.fromkeys(
                [
                    candidate_label,
                    existing_label,
                ]
            )
        )

        if candidate_evidence > existing_evidence:
            return "candidate"

        if existing_evidence > candidate_evidence:
            return "existing"

        if candidate_score >= existing_score:
            return "candidate"

        return "existing"
    
    @staticmethod
    def _is_contextual_noise_entity(
        entity: Dict,
        entities: List[Dict],
        text: str,
    ) -> bool:

        entity_text = str(
            entity.get("text", "")
        ).strip()

        normalized = " ".join(
            entity_text.split()
        ).lower()

        if not normalized:
            return True

        tokens = normalized.split()

        if len(tokens) != 1:
            return False

        score = float(
            entity.get("score", 0.0)
        )

        if score >= 0.90:
            return False

        start = int(entity["start"])
        end = int(entity["end"])

        nearby_entities = []

        for other in entities:
            if other is entity:
                continue

            other_start = int(other["start"])
            other_end = int(other["end"])

            distance = min(
                abs(start - other_end),
                abs(other_start - end),
            )

            if distance <= 2:
                nearby_entities.append(other)

        if not nearby_entities:
            return False

        return True
    
    def _refine_entities(
        self,
        entities: List[Dict],
        text: str,
    ) -> List[Dict]:

        if not entities:
            return []

        refined: List[Dict] = []

        for entity in entities:

            if self._is_invalid_entity_text(entity):
                logger.debug(
                    "Dropping semantically invalid entity: "
                    f"{entity.get('text')!r} "
                    f"({entity.get('label')})"
                )
                continue

            if self._is_contextual_noise_entity(
                entity,
                entities,
                text,
            ):
                logger.debug(
                    "Dropping contextual NER noise: "
                    f"{entity.get('text')!r} "
                    f"({entity.get('label')}) "
                    f"score={entity.get('score')}"
                )
                continue

            refined.append(entity)

        return refined
    
    def _reconstruct_entities(
        self,
        entities: List[Dict],
        text: str,
    ) -> List[Dict]:

        if not entities:
            return []

        reconstructed: List[Dict] = []

        for entity in sorted(
            entities,
            key=lambda item: (
                int(item["start"]),
                int(item["end"]),
            ),
        ):
            start = int(entity["start"])
            end = int(entity["end"])

            if start < 0 or end <= start:
                continue

            entity_copy = dict(entity)
            entity_copy["text"] = text[start:end]

            reconstructed.append(
                entity_copy
            )

        return reconstructed
    
    @staticmethod
    def _is_invalid_entity_text(
        entity: Dict,
    ) -> bool:

        text = str(
            entity.get("text", "")
        ).strip()

        if not text:
            return True

        normalized = " ".join(
            text.split()
        )

        if not normalized:
            return True

        if not any(
            character.isalnum()
            for character in normalized
        ):
            return True

        start = entity.get("start")
        end = entity.get("end")

        if start is None or end is None:
            return True

        if int(end) <= int(start):
            return True

        tokens = normalized.split()

        if len(tokens) == 1:
            token = tokens[0]

            if len(token) <= 1:
                return True

        semantic_tokens = [
            token
            for token in tokens
            if any(
                character.isalnum()
                for character in token
            )
            and len(token) > 1
        ]

        if not semantic_tokens:
            return True

        semantic_ratio = (
            len(semantic_tokens)
            / len(tokens)
        )

        if len(tokens) >= 2 and semantic_ratio < 0.5:
            return True

        return False