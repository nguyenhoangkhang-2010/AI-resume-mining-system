from unittest.mock import Mock


from app.resume_processing.pipelines.resume_pipeline import (
    ResumePipeline
)



def test_resume_pipeline():


    pipeline = ResumePipeline()


    pipeline.parser.extract_text = Mock(
        return_value="""

        John Doe

        john@gmail.com


        EXPERIENCE

        3 years experience


        EDUCATION

        Bachelor Computer Science


        CERTIFICATIONS

        AWS Certified Cloud Practitioner

        """
    )


    result = pipeline.process_pdf(
        "sample.pdf"
    )


    assert "contact" in result

    assert "education" in result

    assert "experience" in result

    assert "certifications" in result