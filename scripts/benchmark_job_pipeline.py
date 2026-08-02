from time import perf_counter

from loguru import logger

from app.job_processing.pipelines.job_pipeline import (
    JobPipeline,
)


SAMPLE_FILE = "data/jobs/sample_job.txt"

ITERATIONS = 20


def benchmark():
    logger.remove()
    logger.add(
        lambda _: None
    )
    pipeline = JobPipeline()

    # Warmup
    pipeline.process(
        SAMPLE_FILE
    )
    start = perf_counter()
    for _ in range(ITERATIONS):
        pipeline.process(
            SAMPLE_FILE
        )
    elapsed = perf_counter() - start
    average_latency = (
        elapsed / ITERATIONS
    ) * 1000
    throughput = (
        ITERATIONS / elapsed
    )
    print(
        f"Average latency : {average_latency:.2f} ms"
    )
    print(
        f"Jobs/sec        : {throughput:.2f}"
    )


if __name__ == "__main__":
    benchmark()