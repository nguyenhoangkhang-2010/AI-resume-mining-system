import re
from typing import Dict, List

from app.extraction.skills.skill_extractor import SkillExtractor

class ExtractionEngine:
    def __init__(self):
        self.skill_extractor = SkillExtractor()
        
        # Basic keywords to identify context blocks
        self.edu_keywords = ["education", "university", "college", "degree", "bachelor", "master", "phd", "academic"]

    def _is_valid_name(self, line: str) -> bool:
        
        line = line.strip()
        
        line_lower = line.casefold()
        
        if not line:
            return False
        
        if not any(char.isalpha() for char in line):
            return False
        
        if len(line) > 50:
            return False

        if "@" in line:
            return False
        
        if "http" in line_lower:
            return False
        
        if "linkedin" in line_lower:
            return False
        
        if "github" in line_lower:
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
        
        if line_lower in invalid_titles:
            return False

        if any(title in line_lower for title in job_titles):
            return False
        
        words = line.split()

        if len(words) > 6:
            return False
        
        digits = re.sub(r"\D", "", line)

        if len(digits) >= 9:
            return False
        
        return True
        
    def _is_valid_school(self, line: str) -> bool:

        line = line.strip()
        
        line_lower = line.casefold()

        if not line:
            return False

        if len(line) < 5:
            return False
        
        if "@" in line:
            return False
        
        if "http" in line_lower:
            return False
        
        invalid_titles = [
            "education",
            "academic background",
            "education background",
            "qualification",
            "qualifications"
        ]

        if line_lower in invalid_titles:
            return False
        
        degree_keywords = [
            "bachelor",
            "master",
            "phd",
            "associate",
            "engineer",
            "mba"
        ]

        if any(keyword in line_lower for keyword in degree_keywords):
            return False
        
        school_keywords = [
            "university",
            "college",
            "institute",
            "academy",
            "school",
            "đại học",
            "cao đẳng",
            "học viện"
        ]
        
        if not any(keyword in line_lower for keyword in school_keywords):
            return False
        
        achievement_keywords = [
            "runner-up",
            "award",
            "competition",
            "contest",
            "certificate",
            "scholarship",
            "prize",
            "achievement",
            "honor"
        ]
        
        if any(keyword in line_lower for keyword in achievement_keywords):
            return False

        if "organized by" in line_lower:
            return False

        if "hosted by" in line_lower:
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
            line_lower = line.casefold()
            if any(keyword in line_lower for keyword in self.edu_keywords):
                if len(line.strip()) > 10:  # Ignore pure headers
                    # Wrap the extracted string into the expected schema object
                    if self._is_valid_school(line):
                        education.append({
                            "school": line.strip(),
                            "degree": "Unknown"
                        })
        return education[:3]  # Return top matches

    def _is_valid_role(self, line: str) -> bool:

        line = line.strip()
        
        line_lower = line.casefold()
        
        if not line:
            return False
        
        invalid_titles = [
            "experience",
            "work experience",
            "professional experience",
            "employment",
            "employment history",
            "career history",
            "work history",
            "career",
            "career objective",
            "objective",
            "summary",
            "profile",
            "education",
            "skills",
            "projects",
            "activities",
            "certificates",
            "awards",
            "references",
            "languages",
            "interests",
            "responsibilities",
            "responsibility",
            "duties",
            "overview",
            "academic projects",
            "project",
            "projects"
        ]
        
        school_keywords = [
            "university",
            "college",
            "academy",
            "institute",
            "school",
            "đại học",
            "cao đẳng",
            "học viện"
        ]
        
        months = [
            "jan", "feb", "mar", "apr", "may", "jun",
            "jul", "aug", "sep", "oct", "nov", "dec",
            "present"
        ]
        
        if "@" in line:
            return False
        
        if "http" in line_lower:
            return False

        if "linkedin" in line_lower:
            return False

        if "github" in line_lower:
            return False
        
        if "score" in line_lower:
            return False

        if "gpa" in line_lower:
            return False
        
        digits = re.sub(r"\D", "", line)

        if len(digits) >= 9:
            return False
        
        if not any(char.isalpha() for char in line):
            return False

        if re.fullmatch(r"[\d\s\-/]+", line):
            return False

        if line_lower in invalid_titles:
            return False

        if len(line) < 3:
            return False
        
        words = line.split()

        if len(words) > 10:
            return False
        
        if any(keyword in line_lower for keyword in school_keywords):
            return False

        if any(month in line_lower for month in months):
            return False

        if "graduation" in line_lower:
            return False

        if "expected" in line_lower:
            return False
        
        return True

    def extract_experience(self, text: str) -> List[Dict[str, str]]:
        """Extract experience context blocks using heuristic keyword matching."""
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        
        experience = []
        
        inside_experience = False
        
        section_headers = [
            "education",
            "skills",
            "projects",
            "activities",
            "certificates",
            "awards",
            "references",
            "languages",
            "interests",
            "summary",
            "profile",
            "objective",
            "career objective",
            "academic",
            "publications",
            "honors",
            "achievements",
            "volunteer",
            "leadership",
            "academic projects",
            "projects",
            "project",
            "education",
            "certifications",
            "academic achievements"
        ]
        
        experience_headers = [
            "experience",
            "work experience",
            "professional experience",
            "employment history"
        ]
        
        for line in lines:
            line_lower = line.casefold()
            
            if line_lower in experience_headers:
                inside_experience = True
                continue
            
            if line_lower in section_headers:
                inside_experience = False
                continue
            
            if inside_experience and self._is_valid_role(line):
                experience.append({
                    "company": "Unknown",
                    "role": line.strip()
                })
            
        return experience[:5]  # Return top matches

    def extract_skills(self, text: str) -> List[str]:
        skills = self.skill_extractor.extract(text)
        return skills if skills else ["General Skills"]