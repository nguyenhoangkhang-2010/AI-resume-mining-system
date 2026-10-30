"""
Synthetic CVs from several industries in several page layouts.

cv_corpus.py varies heading style and column count on software-engineer
content. Real CVs also differ in what the person does (a nurse's CV does not
use the words of an engineer's), in how the page is built (sidebar on the
right, a banner above two columns, dates in a left-hand timeline column,
many pages) and in the order of the sections. This corpus varies all of
those, and also carries sections the parser does not extract (languages,
interests, references) so that text in them must not leak into the real
sections.

Every document is a real PDF; the true section of each body line and the
entities (companies, roles, schools, skills ...) are known. The content is
synthetic: it measures sensitivity to layout and vocabulary, not accuracy on
real resumes.
"""

import random
import textwrap
from dataclasses import dataclass, field
from itertools import product
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import fitz

from app.evaluation.cv_corpus import (
    HEADING_STYLES,
    LAYOUTS as BASE_LAYOUTS,
    LINE_PITCH,
    PAGE_TOP,
    CorpusDocument,
    HeadingStyle,
    TruthLine,
    _font_sources,
    _Writer,
    register_fonts,
)

LAYOUTS = (
    "single",
    "two_column",
    "sidebar_right",
    "banner_two_column",
    "timeline",
    "long",
)

LANGUAGES = ("en", "vi")

STANDARD = "standard"
INDUSTRY = "industry"

assert set(BASE_LAYOUTS) - {"multi_page"} <= set(LAYOUTS)


@dataclass(frozen=True)
class Industry:
    name: str
    roles: Dict[str, List[str]]
    companies: List[str]
    schools: Dict[str, List[str]]
    degrees: Dict[str, List[str]]
    skills: List[str]
    verbs: Dict[str, List[str]]
    objects: Dict[str, List[str]]
    certificates: Dict[str, List[str]]
    summary: Dict[str, str]
    projects: Dict[str, List[str]]
    # Section -> heading used when the wording is "industry".
    headings: Dict[str, Dict[str, str]]


INDUSTRIES: Dict[str, Industry] = {
    industry.name: industry
    for industry in [
        Industry(
            name="software",
            roles={
                "en": ["Backend Engineer", "Data Engineer", "DevOps Engineer"],
                "vi": ["Kỹ sư phần mềm", "Kỹ sư dữ liệu", "Kỹ sư DevOps"],
            },
            companies=["Northwind Labs", "Bluepeak Systems", "Orchid Software", "Helix Digital"],
            schools={
                "en": ["Hanoi University of Science", "Da Nang University of Technology"],
                "vi": ["Đại học Bách khoa Hà Nội", "Đại học Công nghệ Thông tin"],
            },
            degrees={
                "en": ["BSc in Computer Science", "BEng in Software Engineering"],
                "vi": ["Cử nhân Khoa học Máy tính", "Kỹ sư Công nghệ Phần mềm"],
            },
            skills=["Python", "Java", "SQL", "Docker", "Kubernetes", "FastAPI", "PostgreSQL", "Git", "AWS", "Redis"],
            verbs={
                "en": ["Built", "Designed", "Migrated", "Automated"],
                "vi": ["Xây dựng", "Thiết kế", "Chuyển đổi", "Tự động hóa"],
            },
            objects={
                "en": ["payment services", "reporting pipelines", "deployment scripts", "search features"],
                "vi": ["dịch vụ thanh toán", "luồng báo cáo", "tập lệnh triển khai", "tính năng tìm kiếm"],
            },
            certificates={
                "en": ["AWS Certified Cloud Practitioner", "Professional Scrum Master I"],
                "vi": ["Chứng chỉ AWS Cloud Practitioner", "Chứng chỉ Scrum Master"],
            },
            summary={
                "en": "Engineer focused on reliable backend systems and clear communication.",
                "vi": "Kỹ sư tập trung vào hệ thống backend ổn định và giao tiếp rõ ràng.",
            },
            projects={
                "en": ["Order tracking platform", "Log analysis toolkit"],
                "vi": ["Nền tảng theo dõi đơn hàng", "Bộ công cụ phân tích nhật ký"],
            },
            headings={
                "summary": {"en": "Profile", "vi": "Giới thiệu bản thân"},
                "experience": {"en": "Technical Experience", "vi": "Kinh nghiệm kỹ thuật"},
                "education": {"en": "Education", "vi": "Học vấn"},
                "skills": {"en": "Tech Stack", "vi": "Công nghệ sử dụng"},
                "projects": {"en": "Open Source Contributions", "vi": "Dự án mã nguồn mở"},
                "certifications": {"en": "Certificates", "vi": "Chứng chỉ"},
            },
        ),
        Industry(
            name="healthcare",
            roles={
                "en": ["Staff Nurse", "Clinical Nurse Specialist", "Ward Manager"],
                "vi": ["Điều dưỡng viên", "Điều dưỡng chuyên khoa", "Điều dưỡng trưởng"],
            },
            companies=["St Mary General Hospital", "Riverside Medical Centre", "Hanoi Heart Institute", "Sunrise Clinic"],
            schools={
                "en": ["Hanoi Medical University", "Hue University of Medicine"],
                "vi": ["Đại học Y Hà Nội", "Đại học Y Dược Huế"],
            },
            degrees={
                "en": ["BSc in Nursing", "Master of Public Health"],
                "vi": ["Cử nhân Điều dưỡng", "Thạc sĩ Y tế công cộng"],
            },
            skills=["Patient assessment", "Wound care", "IV therapy", "Electronic health records", "Triage", "Infection control", "Medication administration"],
            verbs={
                "en": ["Monitored", "Administered", "Coordinated", "Trained"],
                "vi": ["Theo dõi", "Thực hiện", "Phối hợp", "Hướng dẫn"],
            },
            objects={
                "en": ["post-operative patients", "daily medication rounds", "care plans with doctors", "new nursing staff"],
                "vi": ["bệnh nhân sau phẫu thuật", "lịch phát thuốc hằng ngày", "kế hoạch chăm sóc cùng bác sĩ", "điều dưỡng mới"],
            },
            certificates={
                "en": ["Basic Life Support Certificate", "Advanced Cardiac Life Support"],
                "vi": ["Chứng chỉ hành nghề điều dưỡng", "Chứng chỉ cấp cứu nâng cao"],
            },
            summary={
                "en": "Registered nurse with experience in surgical wards and patient education.",
                "vi": "Điều dưỡng có kinh nghiệm tại khoa ngoại và tư vấn sức khỏe cho bệnh nhân.",
            },
            projects={
                "en": ["Falls prevention programme", "Hand hygiene audit"],
                "vi": ["Chương trình phòng ngừa té ngã", "Kiểm tra vệ sinh tay"],
            },
            headings={
                "summary": {"en": "Professional Profile", "vi": "Hồ sơ nghề nghiệp"},
                "experience": {"en": "Clinical Experience", "vi": "Kinh nghiệm lâm sàng"},
                "education": {"en": "Education and Training", "vi": "Học vấn và đào tạo"},
                "skills": {"en": "Clinical Skills", "vi": "Kỹ năng lâm sàng"},
                "projects": {"en": "Quality Improvement Projects", "vi": "Dự án cải tiến chất lượng"},
                "certifications": {"en": "Licenses and Certifications", "vi": "Giấy phép và chứng chỉ"},
            },
        ),
        Industry(
            name="finance",
            roles={
                "en": ["Financial Analyst", "Senior Accountant", "Risk Manager"],
                "vi": ["Chuyên viên phân tích tài chính", "Kế toán trưởng", "Quản lý rủi ro"],
            },
            companies=["Meridian Capital", "Atlas Audit Partners", "Pacific Trust Bank", "Crown Insurance"],
            schools={
                "en": ["National Economics University", "Foreign Trade University"],
                "vi": ["Đại học Kinh tế Quốc dân", "Đại học Ngoại thương"],
            },
            degrees={
                "en": ["BA in Accounting", "MBA in Finance"],
                "vi": ["Cử nhân Kế toán", "Thạc sĩ Quản trị Kinh doanh"],
            },
            skills=["Financial modelling", "IFRS", "Excel", "Budgeting", "Variance analysis", "SAP", "Credit risk", "Forecasting"],
            verbs={
                "en": ["Prepared", "Reconciled", "Forecast", "Audited"],
                "vi": ["Lập", "Đối chiếu", "Dự báo", "Kiểm toán"],
            },
            objects={
                "en": ["monthly financial statements", "bank and ledger accounts", "quarterly cash flow", "vendor payment controls"],
                "vi": ["báo cáo tài chính hằng tháng", "tài khoản ngân hàng và sổ cái", "dòng tiền hằng quý", "quy trình thanh toán nhà cung cấp"],
            },
            certificates={
                "en": ["Chartered Financial Analyst Level II", "ACCA Diploma in Accounting"],
                "vi": ["Chứng chỉ CFA Level II", "Chứng chỉ ACCA"],
            },
            summary={
                "en": "Finance professional skilled in reporting, forecasting and internal controls.",
                "vi": "Chuyên viên tài chính thành thạo báo cáo, dự báo và kiểm soát nội bộ.",
            },
            projects={
                "en": ["ERP migration for finance team", "Cost reduction review"],
                "vi": ["Chuyển đổi ERP cho khối tài chính", "Rà soát cắt giảm chi phí"],
            },
            headings={
                "summary": {"en": "Executive Summary", "vi": "Tóm tắt điều hành"},
                "experience": {"en": "Professional Experience", "vi": "Kinh nghiệm nghề nghiệp"},
                "education": {"en": "Education", "vi": "Trình độ học vấn"},
                "skills": {"en": "Core Competencies", "vi": "Năng lực cốt lõi"},
                "projects": {"en": "Key Engagements", "vi": "Dự án tiêu biểu"},
                "certifications": {"en": "Licenses and Designations", "vi": "Chứng chỉ nghề nghiệp"},
            },
        ),
        Industry(
            name="marketing",
            roles={
                "en": ["Digital Marketing Specialist", "Content Lead", "Brand Manager"],
                "vi": ["Chuyên viên marketing số", "Trưởng nhóm nội dung", "Quản lý thương hiệu"],
            },
            companies=["Brightside Agency", "Pixel & Pine", "Lotus Media Group", "Orbit Commerce"],
            schools={
                "en": ["Banking Academy", "RMIT University Vietnam"],
                "vi": ["Học viện Ngân hàng", "Đại học RMIT Việt Nam"],
            },
            degrees={
                "en": ["BA in Marketing", "BA in Communications"],
                "vi": ["Cử nhân Marketing", "Cử nhân Truyền thông"],
            },
            skills=["SEO", "Google Analytics", "Copywriting", "Meta Ads", "Email marketing", "Content strategy", "Canva", "A/B testing"],
            verbs={
                "en": ["Launched", "Grew", "Managed", "Optimised"],
                "vi": ["Triển khai", "Tăng trưởng", "Quản lý", "Tối ưu"],
            },
            objects={
                "en": ["paid social campaigns", "organic search traffic", "the content calendar", "email onboarding flows"],
                "vi": ["chiến dịch quảng cáo mạng xã hội", "lượng truy cập tìm kiếm tự nhiên", "lịch nội dung", "chuỗi email chào mừng"],
            },
            certificates={
                "en": ["Google Ads Search Certification", "HubSpot Inbound Marketing"],
                "vi": ["Chứng chỉ Google Ads", "Chứng chỉ HubSpot Inbound"],
            },
            summary={
                "en": "Marketer who turns audience data into campaigns that bring in customers.",
                "vi": "Chuyên viên marketing biến dữ liệu khách hàng thành chiến dịch hiệu quả.",
            },
            projects={
                "en": ["Spring product launch campaign", "Brand refresh"],
                "vi": ["Chiến dịch ra mắt sản phẩm mùa xuân", "Làm mới thương hiệu"],
            },
            headings={
                "summary": {"en": "About Me", "vi": "Về tôi"},
                "experience": {"en": "Career History", "vi": "Lịch sử nghề nghiệp"},
                "education": {"en": "Academic Background", "vi": "Nền tảng học thuật"},
                "skills": {"en": "Tools and Platforms", "vi": "Công cụ và nền tảng"},
                "projects": {"en": "Campaigns", "vi": "Chiến dịch"},
                "certifications": {"en": "Courses and Certificates", "vi": "Khóa học và chứng chỉ"},
            },
        ),
        Industry(
            name="mechanical",
            roles={
                "en": ["Mechanical Design Engineer", "Maintenance Supervisor", "Production Engineer"],
                "vi": ["Kỹ sư thiết kế cơ khí", "Giám sát bảo trì", "Kỹ sư sản xuất"],
            },
            companies=["Titan Precision Works", "Eastern Gear Industries", "Vinh Steel Fabrication", "Apex Automation"],
            schools={
                "en": ["Hanoi University of Science and Technology", "Ho Chi Minh City University of Technology"],
                "vi": ["Đại học Bách khoa Hà Nội", "Đại học Bách khoa TP.HCM"],
            },
            degrees={
                "en": ["BEng in Mechanical Engineering", "BEng in Mechatronics"],
                "vi": ["Kỹ sư Cơ khí", "Kỹ sư Cơ điện tử"],
            },
            skills=["SolidWorks", "AutoCAD", "GD&T", "FEA", "Lean manufacturing", "CNC programming", "PLC basics", "Six Sigma"],
            verbs={
                "en": ["Designed", "Reduced", "Commissioned", "Inspected"],
                "vi": ["Thiết kế", "Giảm", "Vận hành thử", "Kiểm tra"],
            },
            objects={
                "en": ["gearbox housings", "machine downtime", "new assembly lines", "weld quality on site"],
                "vi": ["vỏ hộp số", "thời gian dừng máy", "dây chuyền lắp ráp mới", "chất lượng mối hàn tại công trường"],
            },
            certificates={
                "en": ["Six Sigma Green Belt", "Certified SolidWorks Professional"],
                "vi": ["Chứng chỉ Six Sigma Green Belt", "Chứng chỉ SolidWorks chuyên nghiệp"],
            },
            summary={
                "en": "Mechanical engineer with plant experience in design, maintenance and process improvement.",
                "vi": "Kỹ sư cơ khí có kinh nghiệm thiết kế, bảo trì và cải tiến quy trình tại nhà máy.",
            },
            projects={
                "en": ["Conveyor redesign", "Predictive maintenance pilot"],
                "vi": ["Thiết kế lại băng tải", "Thí điểm bảo trì dự đoán"],
            },
            headings={
                "summary": {"en": "Career Objective", "vi": "Mục tiêu nghề nghiệp"},
                "experience": {"en": "Employment History", "vi": "Quá trình công tác"},
                "education": {"en": "Qualifications", "vi": "Bằng cấp"},
                "skills": {"en": "Technical Skills", "vi": "Kỹ năng kỹ thuật"},
                "projects": {"en": "Engineering Projects", "vi": "Dự án kỹ thuật"},
                "certifications": {"en": "Certifications", "vi": "Chứng chỉ"},
            },
        ),
        Industry(
            name="education",
            roles={
                "en": ["Secondary School Teacher", "Curriculum Coordinator", "Teaching Assistant"],
                "vi": ["Giáo viên trung học", "Điều phối chương trình", "Trợ giảng"],
            },
            companies=["Greenfield High School", "Lac Hong Language Centre", "Sunflower International School", "Hanoi Tutoring Hub"],
            schools={
                "en": ["Hanoi National University of Education", "Ho Chi Minh City University of Pedagogy"],
                "vi": ["Đại học Sư phạm Hà Nội", "Đại học Sư phạm TP.HCM"],
            },
            degrees={
                "en": ["BEd in English Language Teaching", "MEd in Curriculum Design"],
                "vi": ["Cử nhân Sư phạm Tiếng Anh", "Thạc sĩ Lý luận và phương pháp dạy học"],
            },
            skills=["Lesson planning", "Classroom management", "Assessment design", "Differentiated instruction", "Google Classroom", "Parent communication"],
            verbs={
                "en": ["Taught", "Developed", "Mentored", "Assessed"],
                "vi": ["Giảng dạy", "Xây dựng", "Kèm cặp", "Đánh giá"],
            },
            objects={
                "en": ["grade 10 English classes", "a project-based curriculum", "new teachers", "student writing progress"],
                "vi": ["các lớp tiếng Anh khối 10", "chương trình học theo dự án", "giáo viên mới", "tiến bộ viết của học sinh"],
            },
            certificates={
                "en": ["TESOL Certificate", "Teaching Credential in Secondary Education"],
                "vi": ["Chứng chỉ TESOL", "Chứng chỉ nghiệp vụ sư phạm"],
            },
            summary={
                "en": "Teacher who builds confident learners through clear goals and steady feedback.",
                "vi": "Giáo viên giúp học sinh tự tin hơn nhờ mục tiêu rõ ràng và phản hồi đều đặn.",
            },
            projects={
                "en": ["School reading programme", "Peer tutoring scheme"],
                "vi": ["Chương trình đọc sách của trường", "Mô hình học sinh kèm nhau"],
            },
            headings={
                "summary": {"en": "Personal Statement", "vi": "Giới thiệu"},
                "experience": {"en": "Teaching Experience", "vi": "Kinh nghiệm giảng dạy"},
                "education": {"en": "Qualifications", "vi": "Trình độ đào tạo"},
                "skills": {"en": "Areas of Expertise", "vi": "Lĩnh vực chuyên môn"},
                "projects": {"en": "Curriculum Projects", "vi": "Dự án chương trình học"},
                "certifications": {"en": "Teaching Credentials", "vi": "Chứng chỉ giảng dạy"},
            },
        ),
    ]
}

# Sections that are not extracted: their lines must stay out of the real
# sections. "Awards" is part of certifications in the heading lexicon.
EXTRA_TITLES: Dict[str, Dict[str, Tuple[str, str]]] = {
    # key -> language -> (heading, truth section)
    "languages": {"en": ("Languages", "other"), "vi": ("Ngoại ngữ", "other")},
    "interests": {"en": ("Interests", "other"), "vi": ("Sở thích", "other")},
    "references": {"en": ("References", "other"), "vi": ("Người tham chiếu", "other")},
    "publications": {"en": ("Publications", "other"), "vi": ("Công bố khoa học", "other")},
    "memberships": {"en": ("Professional Memberships", "other"), "vi": ("Hội viên tổ chức nghề nghiệp", "other")},
    "awards": {"en": ("Awards", "certifications"), "vi": ("Giải thưởng", "certifications")},
}

STANDARD_TITLES: Dict[str, Dict[str, str]] = {
    "summary": {"en": "Summary", "vi": "Mục tiêu nghề nghiệp"},
    "experience": {"en": "Work Experience", "vi": "Kinh nghiệm làm việc"},
    "education": {"en": "Education", "vi": "Học vấn"},
    "skills": {"en": "Skills", "vi": "Kỹ năng"},
    "projects": {"en": "Projects", "vi": "Dự án"},
    "certifications": {"en": "Certifications", "vi": "Chứng chỉ"},
}

EXTRA_BODY: Dict[str, Dict[str, List[str]]] = {
    "languages": {
        "en": ["English - professional working proficiency", "Vietnamese - native"],
        "vi": ["Tiếng Anh - giao tiếp công việc", "Tiếng Việt - bản ngữ"],
    },
    "interests": {
        "en": ["Trail running and photography", "Volunteer cooking on weekends"],
        "vi": ["Chạy bộ và chụp ảnh", "Nấu ăn thiện nguyện cuối tuần"],
    },
    "references": {
        "en": ["Available on request", "Contact details supplied at interview"],
        "vi": ["Cung cấp khi có yêu cầu", "Thông tin liên hệ cung cấp khi phỏng vấn"],
    },
    "publications": {
        "en": ["Practical notes on process improvement, trade journal, 2022", "Conference poster on workflow design, 2021"],
        "vi": ["Ghi chép thực tế về cải tiến quy trình, tạp chí ngành, 2022", "Poster hội thảo về thiết kế quy trình, 2021"],
    },
    "memberships": {
        "en": ["Member of the national professional association", "Volunteer mentor in the alumni network"],
        "vi": ["Hội viên hiệp hội nghề nghiệp quốc gia", "Cố vấn tình nguyện của mạng lưới cựu sinh viên"],
    },
    "awards": {
        "en": ["Employee of the Year 2023", "Dean's list for three semesters"],
        "vi": ["Nhân viên xuất sắc năm 2023", "Danh sách xuất sắc của khoa ba học kỳ"],
    },
}

NAMES = [
    "Nguyen Thi Lan", "Tran Van Hung", "Le Minh Chau", "Pham Quoc Bao",
    "Hoang Thu Ha", "Vu Duc Anh",
]
CITIES = ["Ha Noi", "Hai Phong", "Da Nang", "Ho Chi Minh City"]


@dataclass
class Job:
    header: str
    dates: str
    bullets: List[str]
    company: str
    role: str


@dataclass
class IndustryDocument(CorpusDocument):
    industry: str = "software"
    entities: Dict[str, List[str]] = field(default_factory=dict)
    section_order: List[str] = field(default_factory=list)
    # (heading text as drawn, section it introduces) for every heading
    headings: List[Tuple[str, str]] = field(default_factory=list)


class _Builder:
    """Generated content for one document."""

    def __init__(
        self,
        rng: random.Random,
        industry: Industry,
        language: str,
        width: int,
        jobs: Tuple[int, int],
    ):
        self.rng = rng
        self.industry = industry
        self.language = language
        self.width = width
        self.jobs_range = jobs
        self._used: set = set()

    def _unique(self, line: str) -> str:
        candidate = line
        counter = 2

        while candidate in self._used:
            candidate = f"{line} ({counter})"
            counter += 1

        self._used.add(candidate)

        return candidate

    def _wrap(self, text: str) -> List[str]:
        return [self._unique(line) for line in textwrap.wrap(text, self.width)]

    def _bullet(self) -> List[str]:
        industry, lang = self.industry, self.language
        text = (
            f"- {self.rng.choice(industry.verbs[lang])} "
            f"{self.rng.choice(industry.objects[lang])}"
        )

        return self._wrap(text)

    def experience(self) -> List[Job]:
        industry, lang = self.industry, self.language
        year = 2025
        jobs: List[Job] = []

        for _ in range(self.rng.randint(*self.jobs_range)):
            span = self.rng.randint(1, 3)
            role = self.rng.choice(industry.roles[lang])
            company = self.rng.choice(industry.companies)
            bullets: List[str] = []

            for _ in range(self.rng.randint(2, 3)):
                bullets.extend(self._bullet())

            jobs.append(
                Job(
                    header=self._unique(f"{role} - {company}"),
                    dates=self._unique(f"{year - span} - {year}"),
                    bullets=bullets,
                    company=company,
                    role=role,
                )
            )

            year -= span

        return jobs

    def education(self) -> Tuple[List[str], List[str], List[str]]:
        industry, lang = self.industry, self.language
        degree = self.rng.choice(industry.degrees[lang])
        school = self.rng.choice(industry.schools[lang])

        return (
            [self._unique(degree), self._unique(school), self._unique("2015 - 2019")],
            [school],
            [degree],
        )

    def projects(self) -> List[str]:
        label = "Project" if self.language == "en" else "Dự án"
        names = self.industry.projects[self.language]
        lines: List[str] = []

        for index, name in enumerate(self.rng.sample(names, k=self.rng.randint(1, len(names)))):
            lines.append(self._unique(f"{label} {chr(65 + index)}: {name}"))
            lines.extend(self._bullet())

        return lines


def _flat_job(job: Job) -> List[str]:
    return [job.header, job.dates, *job.bullets]


@dataclass(frozen=True)
class Variant:
    industry: str
    layout: str
    language: str
    wording: str


class IndustryCorpusBuilder:

    def __init__(
        self,
        seed: int = 7,
        per_variant: int = 1,
        industries: Optional[Sequence[str]] = None,
        layouts: Optional[Sequence[str]] = None,
        wordings: Sequence[str] = (STANDARD, INDUSTRY),
    ):
        self.seed = seed
        self.per_variant = per_variant
        self.industries = list(industries or INDUSTRIES)
        self.layouts = list(layouts or LAYOUTS)
        self.wordings = list(wordings)

    def variants(self) -> List[Variant]:
        languages = [
            language for language in LANGUAGES if _font_sources(language) is not None
        ]

        return [
            Variant(industry, layout, language, wording)
            for industry, layout, language, wording in product(
                self.industries, self.layouts, languages, self.wordings
            )
        ]

    def build(self, directory: Path) -> List[IndustryDocument]:
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)

        documents: List[IndustryDocument] = []

        for variant in self.variants():
            for index in range(self.per_variant):
                documents.append(self._build_one(directory, variant, index))

        return documents

    def _build_one(
        self, directory: Path, variant: Variant, index: int
    ) -> IndustryDocument:
        key = (
            f"{self.seed}-{variant.industry}-{variant.layout}-"
            f"{variant.language}-{variant.wording}-{index}"
        )
        rng = random.Random(key)
        industry = INDUSTRIES[variant.industry]
        lang = variant.language

        narrow = variant.layout in ("two_column", "sidebar_right", "banner_two_column")
        width = 60 if narrow else 78
        sidebar_width = 28
        jobs = (6, 8) if variant.layout == "long" else (2, 3)

        if narrow:
            jobs = (2, 2)  # the columns do not flow onto a second page

        main = _Builder(rng, industry, lang, width, jobs)
        side = _Builder(rng, industry, lang, sidebar_width, jobs)
        side._used = main._used  # truth lines must be unique across columns

        name = rng.choice(NAMES)
        personal = [
            name,
            f"{name.lower().replace(' ', '.')}@example.com",
            f"+84 9{rng.randint(10, 99)} {rng.randint(100, 999)} {rng.randint(100, 999)}",
            rng.choice(CITIES),
        ]

        experience = main.experience()
        education_lines, schools, degrees = main.education()
        skills = rng.sample(industry.skills, k=min(len(industry.skills), rng.randint(5, 8)))
        certs = rng.sample(industry.certificates[lang], k=rng.randint(1, 2))

        skill_builder = side if narrow else main

        body: Dict[str, List[str]] = {
            "summary": main._wrap(industry.summary[lang]),
            "experience": [line for job in experience for line in _flat_job(job)],
            "education": education_lines,
            "skills": skill_builder._wrap(", ".join(skills)),
            "projects": main.projects(),
            "certifications": [
                line for cert in certs for line in skill_builder._wrap(cert)
            ],
        }

        extras = self._pick_extras(rng, variant.layout)

        for key_name in extras:
            body[key_name] = [
                line
                for text in EXTRA_BODY[key_name][lang]
                for line in skill_builder._wrap(text)
            ]

        titles = {
            section: (
                industry.headings[section][lang]
                if variant.wording == INDUSTRY
                else STANDARD_TITLES[section][lang]
            )
            for section in STANDARD_TITLES
        }
        extra_titles = {key_name: EXTRA_TITLES[key_name][lang][0] for key_name in extras}

        identifier = (
            f"{variant.wording}__{variant.industry}__{variant.layout}__{lang}__{index}"
        )
        path = directory / f"{identifier}.pdf"
        style = rng.choice(list(HEADING_STYLES))

        order = _section_order(rng, variant.layout, extras)

        _draw(
            path=path,
            personal=personal,
            body=body,
            experience=experience,
            titles={**titles, **extra_titles},
            style=HEADING_STYLES[style],
            layout=variant.layout,
            language=lang,
            order=order,
            sidebar=_sidebar_sections(variant.layout, extras),
        )

        truth = [TruthLine("personal_info", line) for line in personal]

        for section, lines in body.items():
            section_truth = (
                EXTRA_TITLES[section][lang][1] if section in EXTRA_TITLES else section
            )
            truth.extend(TruthLine(section_truth, line) for line in lines)

        all_titles = {**titles, **extra_titles}
        heading_style = HEADING_STYLES[style]
        headings = [
            (
                all_titles[section].upper() if heading_style.upper else all_titles[section],
                EXTRA_TITLES[section][lang][1] if section in EXTRA_TITLES else section,
            )
            for section in order
            if section in body
        ]

        entities = {
            "companies": sorted({job.company for job in experience}),
            "roles": sorted({job.role for job in experience}),
            "schools": schools,
            "degrees": degrees,
            "skills": skills,
            "certifications": certs,
            "name": [name],
        }

        return IndustryDocument(
            id=identifier,
            style=style,
            layout=variant.layout,
            language=lang,
            path=path,
            truth=truth,
            wording=variant.wording,
            industry=variant.industry,
            entities=entities,
            section_order=order,
            headings=headings,
        )

    @staticmethod
    def _pick_extras(rng: random.Random, layout: str) -> List[str]:
        keys = list(EXTRA_TITLES)
        count = rng.randint(2, 4)

        return rng.sample(keys, k=count)


def _section_order(rng: random.Random, layout: str, extras: List[str]) -> List[str]:
    """Order of the main-flow sections: some CVs lead with skills or education."""

    movable = ["experience", "education", "skills", "projects", "certifications"]
    rng.shuffle(movable)

    order = ["summary", *movable]

    for key_name in extras:
        position = rng.randint(2, len(order))
        order.insert(position, key_name)

    # Awards are filed under certifications, wherever they appear.
    return order


def _sidebar_sections(layout: str, extras: List[str]) -> List[str]:
    if layout not in ("two_column", "sidebar_right", "banner_two_column"):
        return []

    return ["skills", "certifications", *[e for e in extras if e in ("languages", "interests", "awards")]]


# ---------------------------------------------------------------- drawing

TIMELINE_DATE_X = 30
TIMELINE_BODY_X = 135
BANNER_HEIGHT = 80


def _draw(
    path: Path,
    personal: List[str],
    body: Dict[str, List[str]],
    experience: List[Job],
    titles: Dict[str, str],
    style: HeadingStyle,
    layout: str,
    language: str,
    order: List[str],
    sidebar: List[str],
) -> None:
    fonts = _font_sources(language)

    if fonts is None:
        raise RuntimeError("No Unicode font available for this language")

    document = fitz.open()
    page = document.new_page()

    if fonts["R"] == "helv":
        writer_fonts = {"R": "helv", "B": "hebo"}
    else:
        writer_fonts = fonts
        register_fonts(page, fonts)

    def heading(writer: _Writer, section: str) -> None:
        title = titles[section]

        writer.gap(style.gap)
        writer.line(title.upper() if style.upper else title, size=style.size, bold=style.bold)

    def section_lines(writer: _Writer, section: str) -> None:
        heading(writer, section)

        for text in body[section]:
            writer.line(text)

    def personal_block(writer: _Writer) -> None:
        writer.line(personal[0], size=16, bold=True)

        for text in personal[1:]:
            writer.line(text)

    def draw_timeline(writer: _Writer, section: str) -> None:
        heading(writer, section)

        if section == "experience":
            for job in experience:
                # Keep a job on one page: its dates and its text share a row.
                writer.keep_together(LINE_PITCH * (len(job.bullets) + 2))

                top = writer.y
                writer.line(job.dates)
                bottom_of_dates = writer.y
                writer.y = top
                writer.x = TIMELINE_BODY_X
                writer.line(job.header)

                for text in job.bullets:
                    writer.line(text)

                writer.x = TIMELINE_DATE_X
                writer.y = max(writer.y, bottom_of_dates) + 4
        else:
            for text in body[section]:
                writer.line(text)

    present = [section for section in order if section in body]

    if layout in ("single", "long"):
        writer = _Writer(
            document, page, 72, writer_fonts, allow_new_pages=True
        )
        personal_block(writer)

        for section in present:
            section_lines(writer, section)

    elif layout == "timeline":
        writer = _Writer(
            document, page, TIMELINE_DATE_X, writer_fonts, allow_new_pages=True
        )
        personal_block(writer)

        for section in present:
            draw_timeline(writer, section)

    else:
        left_x, right_x = (30, 215) if layout != "sidebar_right" else (40, 400)
        side_writer = _Writer(
            document, page, left_x if layout != "sidebar_right" else right_x,
            writer_fonts, allow_new_pages=False,
        )
        main_writer = _Writer(
            document, page, right_x if layout != "sidebar_right" else left_x,
            writer_fonts, allow_new_pages=False,
        )

        if layout == "banner_two_column":
            banner = _Writer(document, page, 72, writer_fonts, allow_new_pages=False)
            personal_block(banner)
            side_writer.y = main_writer.y = PAGE_TOP + BANNER_HEIGHT
        elif layout == "sidebar_right":
            personal_block(main_writer)
        else:
            personal_block(side_writer)

        # Sidebar sections go to the narrow column, the rest to the main one.
        for section in present:
            target = side_writer if section in sidebar else main_writer
            section_lines(target, section)

    document.save(str(path))
    document.close()
