import re
from typing import Dict, List, Any
import json
from pathlib import Path
from loguru import logger

class ExtractionEngine:
    def __init__(self):
        self.dictionary_path = Path("data/dictionaries/skills.json")
        self.known_skills = self._load_skills_dictionary()
        
        # Basic keywords to identify context blocks
        self.edu_keywords = ["education", "university", "college", "degree", "bachelor", "master", "phd", "academic"]
        self.exp_keywords = ["experience", "work", "employment", "history", "project", "role"]

    def _load_skills_dictionary(self) -> List[str]:
        """Load skills from a dynamic JSON dictionary file or create a default extended one."""
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
                json.dump(default_skills, f, indent=4)
        except Exception as e:
            logger.warning(f"Could not save default skills dictionary: {e}")
            
        return default_skills

    def extract_personal_info(self, text: str) -> Dict[str, str]:
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(email_pattern, text)
        email = emails[0] if emails else "unknown@example.com"

        lines = [line.strip() for line in text.split('\n') if line.strip()]
        name = lines[0] if lines else "Unknown Candidate"
        
        if len(name) > 50:
            name = "Unknown Candidate"

        return {"name": name, "email": email}

    def extract_education(self, text: str) -> List[Dict[str, str]]:
        """Extract education context blocks using heuristic keyword matching."""
        lines = text.split('\n')
        education = []
        for line in lines:
            if any(keyword in line.lower() for keyword in self.edu_keywords):
                if len(line.strip()) > 10:  # Ignore pure headers
                    # Wrap the extracted string into the expected schema object
                    education.append({"school": line.strip(), "degree": "Unknown"})
        return education[:3]  # Return top matches

    def extract_experience(self, text: str) -> List[Dict[str, str]]:
        """Extract experience context blocks using heuristic keyword matching."""
        lines = text.split('\n')
        experience = []
        for line in lines:
            if any(keyword in line.lower() for keyword in self.exp_keywords):
                if len(line.strip()) > 10:  # Ignore pure headers
                    # Wrap the extracted string into the expected schema object
                    experience.append({"company": "Unknown", "role": line.strip()})
        return experience[:5]  # Return top matches

    def extract_skills(self, text: str) -> List[str]:
        extracted_skills = []
        for skill in self.known_skills:
            # Negative lookbehinds/lookaheads prevent matching sub-words while allowing special characters (+, #)
            pattern = r'(?i)(?<![a-zA-Z0-9_])' + re.escape(skill) + r'(?![a-zA-Z0-9_])'
            if re.search(pattern, text):
                extracted_skills.append(skill)
        
        return extracted_skills if extracted_skills else ["General IT Skills"]