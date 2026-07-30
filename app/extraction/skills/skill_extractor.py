import re
import json
from typing import List
from loguru import logger
from pathlib import Path


class SkillExtractor:
    def __init__(self):
        self.dictionary_path = Path("data/dictionaries/skills.json")
        self.skills = self._load_dictionary()

    def _load_dictionary(self) -> List[str]:
        if self.dictionary_path.exists():
            try:
                with open(self.dictionary_path, 'r', encoding='utf-8') as f:
                    skills = json.load(f)
                    logger.info(f"Loaded {len(skills)} skills from dynamic dictionary.")
                    return skills
            except Exception as e:
                logger.error(f"Failed to load skills dictionary: {e}")
        
        # Extended fallback list covering many IT domains
        default_skills = [
            "Python", "Java", "C++", "C#", "FastAPI", "MongoDB", "SQL",
            "Machine Learning", "Data Science", "Docker", "Kubernetes",
            "AWS", "React", "Node.js", "PyTorch", "TensorFlow", "Git",
            "Pandas", "NumPy", "Matplotlib", "Scikit-Learn", "Django",
            "Flask", "REST API", "GraphQL", "Redis", "PostgreSQL",
            "MySQL", "Linux", "Bash", "Agile", "Scrum", "CI/CD",
            "Tkinter", "OOP", "JSON", "Backend", "Frontend", "Fullstack",
            "Vue.js", "Angular", "HTML", "CSS", "JavaScript", "TypeScript"
        ]
        
        try:
            self.dictionary_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.dictionary_path, 'w', encoding='utf-8') as f:
                json.dump(default_skills, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"Could not save default skills dictionary: {e}")
            
        return default_skills

    def extract(self, text: str) -> List[str]:
        if not text:
            logger.warning("Empty text provided to SkillExtractor.")
            return []
            
        logger.debug("Starting skill extraction process.")
        extracted_skills = set()
        
        for skill in self.skills:
            pattern = r'\b' + re.escape(skill).replace(r'\ ', r'\s+') + r'\b'
            if re.search(pattern, text, re.IGNORECASE):
                extracted_skills.add(skill)
                
        logger.debug(f"Extracted {len(extracted_skills)} skills.")
        return sorted(list(extracted_skills))