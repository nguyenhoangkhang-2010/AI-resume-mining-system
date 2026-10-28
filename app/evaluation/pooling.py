from typing import Dict, List, Mapping, Optional, Protocol, Sequence

import numpy as np


DEFAULT_SECTION_WEIGHTS: Dict[str, float] = {
    "headline": 1.0,
    "skills": 1.0,
    "experience": 1.0,
    "projects": 0.5,
    "responsibilities": 1.0,
}


class Encoder(Protocol):
    def encode(self, texts: Sequence[str]) -> np.ndarray:
        """Returns L2-normalised vectors, one row per text."""


class ProfileEmbedder:
    """
    Embeds a profile as the normalised, weighted mean of the embeddings of
    its sections, so that text beyond the model's token limit is not lost.
    """

    def __init__(
        self,
        encoder: Encoder,
        weights: Optional[Mapping[str, float]] = None,
    ):
        self.encoder = encoder
        self.weights = dict(weights or DEFAULT_SECTION_WEIGHTS)

    def embed(self, sections: Mapping[str, str]) -> np.ndarray:
        return self.embed_many([sections])[0]

    def embed_many(
        self,
        profiles: Sequence[Mapping[str, str]],
    ) -> np.ndarray:
        """
        Embeds many profiles with a single encoder call.
        """

        texts: List[str] = []
        owners: List[tuple[int, float]] = []

        for index, sections in enumerate(profiles):
            for name, text in sections.items():
                if text and text.strip():
                    texts.append(text)
                    owners.append((index, self.weights.get(name, 1.0)))

        vectors = (
            np.asarray(self.encoder.encode(texts), dtype=np.float32)
            if texts
            else np.zeros((0, 0), dtype=np.float32)
        )

        if vectors.size:
            dimension = vectors.shape[1]
        else:
            dimension = np.asarray(self.encoder.encode([""])).shape[1]

        pooled = np.zeros((len(profiles), dimension), dtype=np.float32)

        for (index, weight), vector in zip(owners, vectors):
            pooled[index] += weight * vector

        for index in range(len(profiles)):
            norm = np.linalg.norm(pooled[index])

            if norm == 0:
                # Profile without any text: fall back to the model's
                # embedding of the empty string rather than a zero vector.
                pooled[index] = np.asarray(self.encoder.encode([""])[0])
            else:
                pooled[index] /= norm

        return pooled
