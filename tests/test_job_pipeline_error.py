import pytest

from app.job_processing.pipelines.job_pipeline import (
    JobPipeline,
)

from unittest.mock import Mock

def test_process_none_path():

    pipeline = JobPipeline()

    with pytest.raises(
        ValueError
    ):

        pipeline.process(None)
        
        
def test_parser_exception():

    pipeline = JobPipeline()

    pipeline.parser.parse = Mock(
        side_effect=RuntimeError(
            "Parser failed"
        )
    )

    with pytest.raises(
        RuntimeError
    ):

        pipeline.process(
            "job.txt"
        )