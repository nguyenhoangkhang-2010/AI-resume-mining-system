"""
Synthetic resume/job dataset for offline evaluation.

Relevance labels are derived from latent attributes of each candidate
(role family and years of experience), never from the overlap between
the skills a candidate lists and the skills a job asks for. Skill lists
are generated with noise on top of the latent role: missing core skills,
off-role skills, alias spellings and "keyword stuffers" that list another
role's skills without having that background. Without that separation a
skill-overlap ranker would be scored against labels it effectively
defines.

The data is synthetic: results measure robustness to this noise model
and are not a prediction of real-world accuracy.
"""

import random
from typing import Dict, List, Sequence

from app.evaluation.dataset import (
    EvalCandidate,
    EvalDataset,
    EvalExperience,
    EvalJob,
    ExtractionDocument,
)


END_YEAR = 2025

FAMILIES: Dict[str, Dict[str, List[str]]] = {
    "backend": {
        "title": ["Backend Engineer", "Backend Developer", "Software Engineer"],
        "core": [
            "python", "java", "sql", "postgresql", "docker",
            "rest", "git", "redis", "kubernetes", "aws",
        ],
        "extra": ["fastapi", "django", "spring", "kafka", "mongodb", "graphql"],
    },
    "frontend": {
        "title": ["Frontend Engineer", "Frontend Developer", "UI Engineer"],
        "core": [
            "javascript", "typescript", "react", "html", "css",
            "git", "redux", "next.js", "graphql", "figma",
        ],
        "extra": ["angular", "vue.js", "node.js", "jest"],
    },
    "data_engineering": {
        "title": ["Data Engineer", "Analytics Engineer", "Big Data Engineer"],
        "core": [
            "python", "sql", "spark", "airflow", "kafka",
            "snowflake", "aws", "docker", "dbt", "bigquery",
        ],
        "extra": ["hadoop", "postgresql", "terraform", "git"],
    },
    "ml_engineering": {
        "title": ["Machine Learning Engineer", "ML Engineer", "AI Engineer"],
        "core": [
            "python", "pytorch", "tensorflow", "scikit-learn", "pandas",
            "numpy", "machine learning", "deep learning", "nlp", "docker",
        ],
        "extra": ["sql", "aws", "git", "spark"],
    },
    "devops": {
        "title": ["DevOps Engineer", "Site Reliability Engineer", "Platform Engineer"],
        "core": [
            "docker", "kubernetes", "terraform", "ansible", "jenkins",
            "aws", "linux", "ci/cd", "prometheus", "grafana", "helm", "git",
        ],
        "extra": ["python", "azure", "gcp", "nginx"],
    },
    "mobile": {
        "title": ["Mobile Engineer", "Android Developer", "iOS Developer"],
        "core": [
            "kotlin", "swift", "android", "ios", "flutter",
            "react native", "git", "rest", "graphql", "firebase",
        ],
        "extra": ["java", "typescript"],
    },
}

ADJACENT_FAMILIES = {
    frozenset(pair)
    for pair in [
        ("backend", "data_engineering"),
        ("data_engineering", "ml_engineering"),
        ("backend", "devops"),
        ("frontend", "mobile"),
    ]
}

# Alternative spellings a resume may use for a canonical skill. Only some
# are known to the project's alias dictionary; the rest stay unresolved,
# which is intentional.
SKILL_ALIASES: Dict[str, List[str]] = {
    "javascript": ["js", "javascript es6"],
    "python": ["python3", "py"],
    "kubernetes": ["k8s"],
    "postgresql": ["postgres"],
    "typescript": ["ts"],
    "react": ["reactjs"],
    "machine learning": ["ml"],
    "scikit-learn": ["sklearn"],
    "tensorflow": ["tf"],
    "mongodb": ["mongo"],
    "node.js": ["nodejs"],
}

COMPANIES = [
    "Northwind Labs", "Bluepeak Systems", "Orchid Software", "Helix Digital",
    "Quartz Analytics", "Ember Cloud", "Lumen Works", "Vertex Soft",
]

FILLER_SENTENCES = [
    "Collaborated with product and design teams on quarterly planning.",
    "Reviewed code and mentored junior colleagues.",
    "Improved reliability and reduced incident response time.",
    "Documented architecture decisions for the wider team.",
    "Delivered features on schedule in an agile environment.",
]

BULLET_TEMPLATES = [
    "Built services using {a} and {b}.",
    "Maintained systems written in {a} with {b}.",
    "Designed and shipped a project with {a}.",
    "Worked daily with {a}, {b} and {c}.",
]

SENIORITY_YEARS = (1, 3, 5)

# Noise model. A first version used milder values and every ranker scored
# ~1.0 on family-only labels, which cannot tell rankers apart; the values
# below were raised once for that reason, not tuned towards any ranker.
OFF_ROLE_PROBABILITY = 0.12
CORE_SKILL_PROBABILITY = 0.6
EXTRA_SKILL_PROBABILITY = 0.3
ALIAS_PROBABILITY = 0.35
STUFFER_RATE = 0.15
GENERIC_TITLE_PROBABILITY = 0.4

GENERIC_TITLES = ["Software Engineer", "Software Developer", "Engineer"]


def are_adjacent(first: str, second: str) -> bool:
    return frozenset((first, second)) in ADJACENT_FAMILIES


def relevance_with_seniority(
    job_family: str,
    required_years: int,
    candidate_family: str,
    candidate_years: int,
) -> int:
    """
    Graded relevance (0-3) from latent attributes only.
    """

    if candidate_family == job_family:
        if candidate_years >= required_years:
            return 3

        if candidate_years >= required_years - 1:
            return 2

        return 1

    if are_adjacent(candidate_family, job_family):
        return 1 if candidate_years >= required_years else 0

    return 0


def relevance_family_only(
    job_family: str,
    candidate_family: str,
) -> int:
    """
    Graded relevance (0-2) that ignores seniority entirely.
    """

    if candidate_family == job_family:
        return 2

    if are_adjacent(candidate_family, job_family):
        return 1

    return 0


class SyntheticDatasetGenerator:

    def __init__(
        self,
        seed: int = 42,
        n_candidates: int = 300,
        jobs_per_family: int = 5,
        n_extraction_documents: int = 100,
    ):
        self.seed = seed
        self.n_candidates = n_candidates
        self.jobs_per_family = jobs_per_family
        self.n_extraction_documents = n_extraction_documents
        self.random = random.Random(seed)

    def generate(self) -> EvalDataset:
        jobs = self._generate_jobs()
        candidates = self._generate_candidates()

        qrels = {
            "seniority_aware": self._qrels(
                jobs, candidates, seniority_aware=True
            ),
            "family_only": self._qrels(
                jobs, candidates, seniority_aware=False
            ),
        }

        documents = self._extraction_documents(candidates)

        return EvalDataset(
            jobs=jobs,
            candidates=candidates,
            qrels=qrels,
            extraction_documents=documents,
            seed=self.seed,
        )

    # ------------------------------------------------------------------ jobs

    def _generate_jobs(self) -> List[EvalJob]:
        jobs = []

        for family, spec in FAMILIES.items():
            for index in range(self.jobs_per_family):
                years = SENIORITY_YEARS[index % len(SENIORITY_YEARS)]

                skills = self.random.sample(
                    spec["core"],
                    self.random.randint(5, 7),
                )

                if self.random.random() < 0.3:
                    skills.append(self.random.choice(spec["extra"]))

                title = self.random.choice(spec["title"])
                level = {1: "Junior", 3: "", 5: "Senior"}[years]
                title = f"{level} {title}".strip()

                jobs.append(
                    EvalJob(
                        id=f"job-{family}-{index + 1}",
                        title=title,
                        family=family,
                        description=self._job_description(
                            title, skills, years
                        ),
                        required_skills=skills,
                        experience_years=years,
                    )
                )

        return jobs

    @staticmethod
    def _job_description(
        title: str,
        skills: Sequence[str],
        years: int,
    ) -> str:

        return (
            f"{title}\n\n"
            f"We are hiring a {title.lower()} with at least {years} "
            f"years of experience.\n\n"
            f"Requirements\n\n" + "\n".join(skills) + "\n\n"
            "Responsibilities\n\n"
            "Build and maintain production systems\n"
            "Collaborate with product and design teams\n"
        )

    # ------------------------------------------------------------ candidates

    def _generate_candidates(self) -> List[EvalCandidate]:
        families = list(FAMILIES)
        candidates = []

        for index in range(self.n_candidates):
            family = families[index % len(families)]
            years = self.random.choice([0, 1, 2, 3, 4, 5, 6, 8, 10])
            stuffer = self.random.random() < STUFFER_RATE

            skills = self._candidate_skills(family, stuffer)

            title = self.random.choice(
                GENERIC_TITLES
                if self.random.random() < GENERIC_TITLE_PROBABILITY
                else FAMILIES[family]["title"]
            )
            experience = self._experience(title, years, skills)

            canonical = list(skills)

            candidates.append(
                EvalCandidate(
                    id=f"cand-{index + 1:04d}",
                    title=title,
                    summary=(
                        f"{title} with {years} years of experience in "
                        f"{', '.join(canonical[:3])}."
                    ),
                    skills=[self._surface_form(skill) for skill in canonical],
                    experience=experience,
                    meta={
                        "family": family,
                        "years": years,
                        "stuffer": stuffer,
                        "canonical_skills": canonical,
                    },
                )
            )

        return candidates

    def _candidate_skills(
        self,
        family: str,
        stuffer: bool,
    ) -> List[str]:

        spec = FAMILIES[family]

        skills = [
            skill
            for skill in spec["core"]
            if self.random.random() < CORE_SKILL_PROBABILITY
        ]

        skills += [
            skill
            for skill in spec["extra"]
            if self.random.random() < EXTRA_SKILL_PROBABILITY
        ]

        for other, other_spec in FAMILIES.items():
            if other == family:
                continue

            skills += [
                skill
                for skill in other_spec["core"]
                if self.random.random() < OFF_ROLE_PROBABILITY
            ]

        if stuffer:
            target = self.random.choice(
                [name for name in FAMILIES if name != family]
            )
            skills += self.random.sample(
                FAMILIES[target]["core"],
                self.random.randint(5, 7),
            )

        unique = list(dict.fromkeys(skills))

        if len(unique) < 4:
            unique += self.random.sample(spec["core"], 4 - len(unique))
            unique = list(dict.fromkeys(unique))

        self.random.shuffle(unique)

        return unique

    def _surface_form(self, skill: str) -> str:
        aliases = SKILL_ALIASES.get(skill)

        if aliases and self.random.random() < ALIAS_PROBABILITY:
            return self.random.choice(aliases)

        return skill

    def _experience(
        self,
        title: str,
        years: int,
        skills: Sequence[str],
    ) -> List[EvalExperience]:

        if years == 0:
            boundaries = [END_YEAR, END_YEAR]
        else:
            jobs_count = min(years, self.random.randint(1, 3))
            cuts = sorted(
                self.random.sample(range(1, years), jobs_count - 1)
            ) if jobs_count > 1 else []
            boundaries = [END_YEAR - years] + [
                END_YEAR - years + cut for cut in cuts
            ] + [END_YEAR]

        entries = []

        for start, end in zip(boundaries, boundaries[1:]):
            picked = self.random.sample(
                list(skills),
                min(3, len(skills)),
            )

            while len(picked) < 3:
                picked.append(picked[0])

            bullet = self.random.choice(BULLET_TEMPLATES).format(
                a=picked[0], b=picked[1], c=picked[2]
            )

            entries.append(
                EvalExperience(
                    role=title,
                    company=self.random.choice(COMPANIES),
                    start_date=str(start),
                    end_date=str(end),
                    description=[
                        bullet,
                        self.random.choice(FILLER_SENTENCES),
                    ],
                )
            )

        return entries

    # ----------------------------------------------------------------- qrels

    @staticmethod
    def _qrels(
        jobs: Sequence[EvalJob],
        candidates: Sequence[EvalCandidate],
        seniority_aware: bool,
    ) -> Dict[str, Dict[str, int]]:

        qrels: Dict[str, Dict[str, int]] = {}

        for job in jobs:
            grades = {}

            for candidate in candidates:
                family = candidate.meta["family"]

                if seniority_aware:
                    grade = relevance_with_seniority(
                        job.family,
                        job.experience_years or 0,
                        family,
                        candidate.meta["years"],
                    )
                else:
                    grade = relevance_family_only(job.family, family)

                if grade > 0:
                    grades[candidate.id] = grade

            qrels[job.id] = grades

        return qrels

    # ------------------------------------------------------------ extraction

    def _extraction_documents(
        self,
        candidates: Sequence[EvalCandidate],
    ) -> List[ExtractionDocument]:

        documents = []

        for candidate in candidates[: self.n_extraction_documents]:
            canonical = candidate.meta["canonical_skills"]
            surface = candidate.skills

            # Titles such as "Android Developer" would mention skills
            # that are not in the gold list, so they are left out.
            lines = ["Skills: " + ", ".join(surface)]

            lines.extend(
                line
                for entry in candidate.experience
                for line in entry.description
            )

            documents.append(
                ExtractionDocument(
                    id=candidate.id,
                    text="\n".join(lines),
                    gold_skills=sorted(set(canonical)),
                )
            )

        return documents
