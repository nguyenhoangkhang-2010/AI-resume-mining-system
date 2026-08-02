from time import perf_counter


class SkillExtractionBenchmark:

    def measure(
        self,
        extractor,
        text: str,
    ) -> dict:

        start = perf_counter()

        skills = extractor.extract(text)

        elapsed = perf_counter() - start

        return {
            "skills": skills,
            "elapsed_seconds": elapsed,
        }