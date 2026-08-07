import re
from typing import Dict, List

from app.extraction.skills.skill_extractor import SkillExtractor
from app.extraction.entity.entity_classifier import EntityClassifier

class ExtractionEngine:
    def __init__(self):
        self.skill_extractor = SkillExtractor()
        self.entity_classifier = EntityClassifier()
        
    def _normalize_header(self, text: str) -> str:
        return text.casefold().strip().rstrip(":")
    
    def classify_entity(
        self,
        text:str,
        context:str | None = None
    ):

        return self.entity_classifier.classify(
            text,
            context
        )

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
    
    def _looks_like_person_name(self, line: str) -> bool:
        line = line.strip()
        if not line:
            return False
        
        words = line.split()

        if not (2 <= len(words) <= 5):
            return False

        if any(char.isdigit() for char in line):
            return False

        lower = line.casefold()

        if any(
            pattern in lower
            for pattern in [
                "@",
                "http",
                "linkedin",
                "github"
            ]
        ):
            return False

        if any(
            word.isupper()
            for word in words
        ):
            return False

        if not all(
            word[0].isupper()
            for word in words
        ):
            return False
        return True
        
    def _role_score_without_person_check(self, line: str) -> int:
        score = 0
        words = line.split()
        
        if len(words) <= 5:
            score += 1

        if any(
            word[:1].isupper()
            for word in words
        ):
            score += 1
        return score
        
    def _role_score(self, line: str) -> int:
        score = 0
        words = line.split()
        if self._is_date_line(line):
            return -10
        if line.startswith("-"):
            return -10
        if len(words) <= 6:
            score += 1
        if len(words) >= 2:
            score += 1
        return score
        
    def _company_score(self, line:str)->int:
        score = 0
        words = line.split()
        if len(words) > 8:
            return -3
        if len(words) >= 2:
            score +=1
        if any(
            word[:1].isupper()
            for word in words
        ):
            score +=1
        return score
    
    def _is_date_line(self, line: str) -> bool:
        pattern = re.compile(
            r"""
            ^
            (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)
            \s+
            \d{4}
            \s*-\s*
            (
                Present
                |
                (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)
                \s+\d{4}
            )
            $
            """,
            re.I | re.X,
        )

        return bool(pattern.match(line.strip()))
    
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

    def _extract_section(self, text: str, headers: List[str]) -> List[str]:
        print("HEADERS =", headers)
        lines = [line.strip() for line in text.split("\n") if line.strip()]

        section_lines = []
        inside_section = False

        common_headers: List[str] = [
            "education",
            "experience",
            "work experience",
            "professional experience",
            "skills",
            "projects",
            "activities",
            "awards",
            "references",
            "languages",
            "interests",
            "summary",
            "profile",
            "objective",
            "certifications",
            "volunteer",
            "leadership",
            "academic projects",
            "projects",
            "education background",
            "academic background",
        ]
        
        headers = {
            self._normalize_header(h)
            for h in headers
        }

        common_headers = {
            self._normalize_header(h)
            for h in common_headers
        }

        for i, line in enumerate(lines):

            normalized = self._normalize_header(line)

            print(
                i,
                normalized,
                "inside=",
                inside_section
            )

            if normalized in headers:
                inside_section = True
                continue

            if inside_section and normalized in common_headers:
                break

            if inside_section:
                section_lines.append(line)

        return section_lines

    def extract_education(self, text: str) -> List[Dict[str, str]]:
        education = []
        
        education_lines = self._extract_section(
            text,
            ["education", "academic background"]
        )
        
        school = None
        degree = None
        duration = None

        for line in education_lines:
            if self._is_valid_school(line):
                school = line
                continue

            if "bachelor" in line.casefold():
                degree = line
                continue

            if self._is_date_line(line):
                duration = line
                continue
            
        if school:
            education.append({
                "school": school,
                "degree": degree or "Unknown",
                "duration": duration
            })

        return education[:3]

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

    def extract_experience(self,text:str):

        experience=[]

        lines=self._extract_section(
            text,
            ["experience"]
        )
        current_company=None
        current_role=None
        current_date=None
        
        for line in lines:
            line=line.strip()
            if not line:
                continue
            print("LINE:",line)
            if self._is_date_line(line):
                current_date=line
                if (
                    current_company
                    and current_role
                ):
                    experience.append(
                        {
                            "company":current_company,
                            "role":current_role,
                            "duration":current_date
                        }
                    )
                    current_company=None
                    current_role=None
                continue
            if line.startswith("-"):
                continue
            if current_company is None:
                current_company=line
                print(
                    "COMPANY:",
                    line
                )
                continue
            if current_role is None:
                current_role=line
                print(
                    "ROLE:",
                    line
                )
                continue
        return experience[:5]

    def extract_skills(self, text: str) -> List[str]:
        skills = self.skill_extractor.extract(text)
        return skills if skills else ["General Skills"]