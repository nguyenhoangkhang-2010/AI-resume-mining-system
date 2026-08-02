from app.extraction.projects.project_extractor import (
    ProjectExtractor
)


def test_project_extraction():

    text = """
    PROJECTS

    AI Resume Mining System

    - Built NLP pipeline using FastAPI
    - Used FAISS semantic search


    EDUCATION

    Bachelor Computer Science
    """


    result = ProjectExtractor.extract(
        text
    )


    assert len(result) == 1

    assert (
        result[0]["name"]
        ==
        "AI Resume Mining System"
    )


    assert (
        "Built NLP pipeline using FastAPI"
        in result[0]["description"]
    )