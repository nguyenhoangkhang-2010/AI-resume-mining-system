import re


class TaxonomyNormalizer:
    """
    Normalize taxonomy names before indexing/searching.
    """

    def normalize(self, value: str) -> str:
        value = value.lower()

        value = re.sub(
            r"[^a-z0-9\s]",
            "",
            value,
        )

        value = re.sub(
            r"\s+",
            " ",
            value,
        )

        return value.strip()