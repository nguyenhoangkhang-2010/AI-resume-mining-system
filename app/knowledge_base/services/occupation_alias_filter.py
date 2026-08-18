class OccupationAliasFilter:

    GENERIC_TOKEN_THRESHOLD = 100


    def filter(
        self,
        canonical: str,
        aliases: list[str],
        token_coverage: dict[str, int],
        total_occupations: int,
    ):

        result = []
        seen = set()

        canonical_norm = (
            canonical
            .casefold()
            .strip()
        )


        for alias in aliases:

            normalized = (
                alias
                .casefold()
                .strip()
            )


            # Rule 1:
            # alias = canonical
            if normalized == canonical_norm:
                continue


            # Rule 2:
            # duplicate
            if normalized in seen:
                continue


            # Rule 3:
            # quá ngắn
            if len(normalized) < 3:
                continue



            words = normalized.split()


            # Rule 4:
            # alias chỉ gồm 1 generic token
            #
            # Ví dụ:
            # Engineer
            # Manager
            # Analyst

            generic_tokens = 0


            for word in words:

                coverage = token_coverage.get(
                    word,
                    0
                )

                if coverage > self.GENERIC_TOKEN_THRESHOLD:
                    generic_tokens += 1


            # alias chỉ toàn token phổ biến
            if generic_tokens == len(words):
                continue
            
            seen.add(normalized)
            result.append(alias)


        return result