from math import sqrt
from typing import List


class CosineSimilarity:
    """
    Calculates cosine similarity between vectors.
    """

    @staticmethod
    def calculate(
        vector_a: List[float],
        vector_b: List[float],
    ) -> float:

        if len(vector_a) != len(vector_b):
            raise ValueError(
                "Vectors must have same dimension"
            )

        if not vector_a:
            return 0.0

        dot_product = sum(
            a * b
            for a, b in zip(vector_a, vector_b)
        )

        magnitude_a = sqrt(
            sum(a * a for a in vector_a)
        )

        magnitude_b = sqrt(
            sum(b * b for b in vector_b)
        )

        if magnitude_a == 0 or magnitude_b == 0:
            return 0.0

        return dot_product / (
            magnitude_a * magnitude_b
        )