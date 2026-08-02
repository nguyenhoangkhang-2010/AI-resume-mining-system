from unittest.mock import Mock
import pytest

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
    
    
def test_resume_pipeline_empty_pdf():
    pipeline = ResumePipeline()

    pipeline.parser.extract_text = Mock(return_value="")

    result = pipeline.process_pdf("sample.pdf")

    assert isinstance(result, dict)

    assert "contact" in result
    assert "summary" in result
    assert "education" in result
    assert "experience" in result
    assert "projects" in result
    assert "certifications" in result
    assert "skills" in result
    
def test_resume_pipeline_parser_exception():
    pipeline = ResumePipeline()

    pipeline.parser.extract_text = Mock(
        side_effect=Exception("PDF parsing failed")
    )

    with pytest.raises(Exception):
        pipeline.process_pdf("sample.pdf")
        
def test_resume_pipeline_contact_only():
    pipeline = ResumePipeline()

    pipeline.parser.extract_text = Mock(
        return_value="""
        John Doe
        john@gmail.com
        +84987654321
        """
    )

    result = pipeline.process_pdf("sample.pdf")

    assert result["contact"]["email"] == "john@gmail.com"
    
def test_resume_pipeline_certification_only():
    pipeline = ResumePipeline()

    pipeline.parser.extract_text = Mock(
        return_value="""
        CERTIFICATIONS

        AWS Certified Cloud Practitioner
        """
    )

    result = pipeline.process_pdf("sample.pdf")

    assert len(result["certifications"]) == 1