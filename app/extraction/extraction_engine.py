import re
from typing import Dict, List

from app.extraction.skills.skill_extractor import SkillExtractor

class ExtractionEngine:
    def __init__(self):
        self.skill_extractor = SkillExtractor()
        
        # Basic keywords to identify context blocks
        self.edu_keywords = ["education", "university", "college", "degree", "bachelor", "master", "phd", "academic"]
        self.exp_keywords = ["experience", "work", "employment", "history", "project", "role"]

    def _is_valid_name(self, line: str) -> bool:
        
        line = line.strip()
        
        if not line:
            return False
        
        if not any(char.isalpha() for char in line):
            return False
        
        if len(line) > 50:
            return False

        if "@" in line:
            return False
        
        if "http" in line.lower():
            return False
        
        if "linkedin" in line.lower():
            return False
        
        if "github" in line.lower():
            return False
        
        invalid_titles = [
            "resume",
            "curriculum vitae",
            "curriculum",
            "cv",
            "portfolio",
            "profile",
            "about me",
            "objective",
            "contact",
            "education",
            "experience",
            "references",
            "reference",
            "skills",
            "language",
            "languages",
            "expertise",
            "summary"
        ]
        
        job_titles = [
            "manager",
            "engineer",
            "developer",
            "designer",
            "analyst",
            "consultant",
            "specialist",
            "coordinator",
            "executive",
            "intern",
            "director",
            "leader"
        ]
        
        if line.lower() in invalid_titles:
            return False
        
        line_lower = line.lower()

        if any(title in line_lower for title in job_titles):
            return False
        
        if not any(char.isalpha() for char in line):
            return False
        
        words = line.split()

        if len(words) > 6:
            return False
        
        digits = re.sub(r"\D", "", line)

        if len(digits) >= 9:
            return False
        
        words = line.split()

        if len(words) > 6:
            return False
        
        return True
        
    def _name_score(self, line: str) -> int:
        score = 0

        words = line.split()

        if 2 <= len(words) <= 4:
            score += 3

        if all(word[:1].isupper() for word in words):
            score += 2

        if len(line) < 35:
            score += 1

        return score    
    
    def extract_personal_info(self, text: str) -> Dict[str, str]:
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(email_pattern, text)
        email = emails[0] if emails else "unknown@example.com"

        lines = [line.strip() for line in text.split('\n') if line.strip()]
        name = "Unknown Candidate"
        
        candidate_names = []

        for line in lines:
            if self._is_valid_name(line):
                candidate_names.append(line)

        if candidate_names:
            name = max(
                candidate_names,
                key=self._name_score
            )
        else:
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