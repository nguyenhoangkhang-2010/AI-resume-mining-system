from typing import Dict, List


class SectionDetector:

    def __init__(self, rules):
        self.section_map = self._build_section_map(
            rules.get("sections", {})
        )

    def _build_section_map(
        self,
        section_rules: Dict[str, List[str]],
    ) -> Dict[str, str]:

        section_map = {}

        for canonical_name, aliases in section_rules.items():

            section_map[
                self.normalize(canonical_name)
            ] = canonical_name

            for alias in aliases:
                section_map[
                    self.normalize(alias)
                ] = canonical_name

        return section_map

    def normalize(
        self,
        text: str,
    ) -> str:

        return (
            text
            .casefold()
            .strip()
            .rstrip(":")
        )

    def detect(
        self,
        text: str,
    ) -> Dict[str, List[str]]:

        lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]

        result: Dict[str, List[str]] = {}

        current_section = None
        preamble: List[str] = []

        for line in lines:

            normalized = self.normalize(line)

            if normalized in self.section_map:

                current_section = self.section_map[
                    normalized
                ]

                result.setdefault(
                    current_section,
                    [],
                )

                continue
            
            if current_section is None:

                preamble.append(line)

                continue

            result[current_section].append(line)

        if preamble:
            result = {
                "personal_info": preamble,
                **result,
            }

        return result