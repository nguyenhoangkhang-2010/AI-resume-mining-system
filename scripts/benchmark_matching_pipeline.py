from time import perf_counter

from loguru import logger

from app.matching.pipelines.matching_pipeline import (
    MatchingPipeline,
)

ITERATIONS = 1000


def benchmark():

    logger.remove()
    logger.add(lambda _: None)

    pipeline = MatchingPipeline()

    # warmup
    pipeline.process(
        candidate_id="candidate-1",
        job_id="job-1",
        skill_score=88,
        semantic_score=91,
    )

    start = perf_counter()

    for _ in range(ITERATIONS):

        pipeline.process(
            candidate_id="candidate-1",
            job_id="job-1",
            skill_score=88,
            semantic_score=91,
        )

    elapsed = perf_counter() - start

    latency = elapsed / ITERATIONS * 1000

    throughput = ITERATIONS / elapsed

    print(f"Average latency : {latency:.2f} ms")
    print(f"Matches/sec     : {throughput:.2f}")


if __name__ == "__main__":
    benchmark()