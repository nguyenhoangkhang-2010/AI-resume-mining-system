import re
from typing import List
from loguru import logger


class SkillExtractor:
    PREDEFINED_SKILLS = [
        "python", "java", "c++", "c#", "javascript", "typescript", "sql", "nosql",
        "machine learning", "deep learning", "data science", "nlp", "computer vision",
        "fastapi", "django", "flask", "react", "angular", "vue",
        "mongodb", "postgresql", "mysql", "redis",
        "docker", "kubernetes", "aws", "gcp", "azure", "ci/cd",
        "pandas", "numpy", "scikit-learn", "pytorch", "tensorflow",
        "agile", "scrum", "communication", "leadership", "problem solving"
    ]

    @staticmethod
    def extract(text: str) -> List[str]:
        if not text:
            logger.warning("Empty text provided to SkillExtractor.")
            return []
            
        logger.debug("Starting skill extraction process.")
        text_lower = text.lower()
        extracted_skills = set()
        
        for skill in SkillExtractor.PREDEFINED_SKILLS:
            pattern = r'\b' + re.escape(skill).replace(r'\ ', r'\s+') + r'\b'
            if re.search(pattern, text_lower):
                extracted_skills.add(skill)
                
        logger.debug(f"Extracted {len(extracted_skills)} skills.")
        return sorted(list(extracted_skills))