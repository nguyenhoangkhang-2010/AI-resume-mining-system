class OccupationAliasGenerator:
    
    MAX_ALIASES = 30

    def generate(
        self,
        occupation_name: str,
        titles: list[str],
    ) -> list[str]:

        aliases = []

        normalized_name = (
            occupation_name
            .casefold()
            .strip()
        )

        for title in titles:

            if not title:
                continue

            cleaned = title.strip()
            
            if self._is_too_long(cleaned):
                continue
            
            if self._has_parentheses(cleaned):
                continue

            normalized_title = (
                cleaned
                .casefold()
            )

            if normalized_title == normalized_name:
                continue

            if cleaned not in aliases:
                aliases.append(cleaned)

        return aliases[:self.MAX_ALIASES]
    
    def _is_too_long(
        self,
        title: str
    ) -> bool:

        return len(title) > 80
    
    def _has_parentheses(
        self,
        title: str
    ) -> bool:

        return (
            "(" in title
            or ")" in title
        )