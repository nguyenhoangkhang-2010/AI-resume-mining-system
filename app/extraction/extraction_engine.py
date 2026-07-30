import re
from typing import Dict, List

from app.extraction.skills.skill_extractor import SkillExtractor

class ExtractionEngine:
    def __init__(self):
        self.skill_extractor = SkillExtractor()
        
        # Basic keywords to identify context blocks
        self.edu_keywords = ["education", "university", "college", "degree", "bachelor", "master", "phd", "academic"]
        self.exp_keywords = ["experience", "work", "employment", "history", "project", "role"]

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
        skills = self.skill_extractor.extract(text)
        return skills if skills else ["General Skills"]