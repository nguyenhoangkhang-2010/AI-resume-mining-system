from pathlib import Path


class JobDescriptionParser:
    def parse(
        self,
        source: str | Path,
    ) -> str:
        """
        Parse a job description from text or file.
        """

        if isinstance(source, Path):
            return source.read_text(
                encoding="utf-8"
            )

        return str(source)