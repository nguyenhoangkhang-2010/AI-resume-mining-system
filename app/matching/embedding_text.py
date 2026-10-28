"""
Builds the text that represents a candidate or a job for embedding.

The embedding model reads at most 128 tokens (roughly 500 characters), and
anything beyond is ignored. The text is therefore built from short named
sections in order of importance, each with its own character budget, so a
long summary cannot push the skills out of the window.
"""

from typing import Any, Dict, Iterable, List


MAX_ROLES = 3
MAX_BULLETS = 8
MAX_PROJECTS = 3

SECTION_CHAR_BUDGET = {
    "headline": 200,
    "skills": 250,
    "experience": 400,
    "projects": 200,
    "responsibilities": 300,
}
DEFAULT_SECTION_CHARS = 300


def _unique(values: Iterable[Any]) -> List[str]:
    seen = set()
    result = []

    for value in values:
        if not isinstance(value, str):
            continue

        value = " ".join(value.split())

        if not value or value.casefold() in seen:
            continue

        seen.add(value.casefold())
        result.append(value)

    return result


def _clip(text: str, section: str) -> str:
    budget = SECTION_CHAR_BUDGET.get(section, DEFAULT_SECTION_CHARS)

    return text[:budget].strip()


def _join_sections(sections: Dict[str, str]) -> str:
    return " ".join(sections.values())


class CandidateTextBuilder:
    """
    Sections: headline (recent roles and summary), skills, experience
    (responsibility and achievement bullets) and projects.
    """

    def sections(self, candidate: Any) -> Dict[str, str]:
        experience = getattr(candidate, "experience", None) or []
        projects = getattr(candidate, "projects", None) or []

        roles = _unique(
            getattr(entry, "role", None) for entry in experience
        )[:MAX_ROLES]

        summary = getattr(candidate, "summary", None) or ""

        headline = ". ".join(
            part for part in (", ".join(roles), summary.strip()) if part
        )

        skills = _unique(
            getattr(candidate, "normalized_skills", None)
            or getattr(candidate, "skills", None)
            or []
        )

        bullets = _unique(
            line
            for entry in experience
            for line in [
                *(getattr(entry, "description", None) or []),
                *(getattr(entry, "achievements", None) or []),
            ]
        )[:MAX_BULLETS]

        project_lines = _unique(
            self._project_line(project) for project in projects
        )[:MAX_PROJECTS]

        sections = {
            "headline": _clip(headline, "headline"),
            "skills": _clip(", ".join(skills), "skills"),
            "experience": _clip(" ".join(bullets), "experience"),
            "projects": _clip("; ".join(project_lines), "projects"),
        }

        return {name: text for name, text in sections.items() if text}

    def text(self, candidate: Any) -> str:
        return _join_sections(self.sections(candidate))

    @staticmethod
    def _project_line(project: Any) -> str:
        title = getattr(project, "title", None) or ""
        technologies = ", ".join(getattr(project, "technologies", None) or [])

        return f"{title}: {technologies}".strip(": ").strip()


class JobTextBuilder:
    """
    Sections: headline (title and occupation), skills and responsibilities.
    The full description is used only when no responsibilities were
    extracted.
    """

    def sections(self, job: Any) -> Dict[str, str]:
        headline = ". ".join(
            part
            for part in (
                getattr(job, "title", None),
                getattr(job, "occupation", None),
            )
            if part
        )

        skills = _unique(
            getattr(job, "normalized_skills", None)
            or getattr(job, "required_skills", None)
            or []
        )

        responsibilities = _unique(getattr(job, "responsibilities", None) or [])

        body = (
            " ".join(responsibilities[:MAX_BULLETS])
            if responsibilities
            else getattr(job, "description", None) or ""
        )

        sections = {
            "headline": _clip(headline, "headline"),
            "skills": _clip(", ".join(skills), "skills"),
            "responsibilities": _clip(body, "responsibilities"),
        }

        return {name: text for name, text in sections.items() if text}

    def text(self, job: Any) -> str:
        return _join_sections(self.sections(job))
