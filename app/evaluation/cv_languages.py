"""
A small synthetic CV set in French, Spanish, German, Portuguese and Russian.

Every CV is a single-column PDF drawn from a hand-written profile of an
invented person, so the true section of each line and the entities (name,
employers, job titles, school, degree, skills, certificate) are known. Each
language has three profiles from different fields; their headings go from
the most common wording to some that no vocabulary file lists.

The set is tiny and written by the same hand that wrote the vocabulary files,
so it shows that the language support works at all (headings, dates, typed
header lines, accented and non-Latin letters), not how accurate it is on real
CVs of those languages.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import fitz

from app.evaluation.cv_corpus import (
    CorpusDocument,
    TruthLine,
    _font_sources,
    _Writer,
    register_fonts,
)

LANGUAGES = ("fr", "es", "de", "pt", "ru")

# (role, company, city, dates, bullets)
Job = Tuple[str, str, str, str, List[str]]


@dataclass(frozen=True)
class Profile:
    name: str
    email: str
    phone: str
    city: str
    summary: str
    jobs: List[Job]
    school: str
    degree: str
    study_dates: str
    skills: List[str]
    certifications: List[str]
    headings: Dict[str, str]


@dataclass
class LanguageDocument(CorpusDocument):
    entities: Dict[str, List[str]] = field(default_factory=dict)


PROFILES: Dict[str, List[Profile]] = {
    "fr": [
        Profile(
            name="Camille Laurent",
            email="camille.laurent@example.com",
            phone="+33 6 12 34 56 78",
            city="Lyon, France",
            summary="Ingénieure logiciel avec six ans d'expérience en développement back-end et en infrastructure cloud.",
            jobs=[
                ("Ingénieure logiciel senior", "Orbis Systèmes SAS", "Lyon", "mars 2020 – aujourd'hui",
                 ["Conception d'API pour le suivi des commandes", "Migration des services vers Kubernetes"]),
                ("Développeuse back-end", "Atelier Numérique SARL", "Grenoble", "septembre 2017 – février 2020",
                 ["Développement de modules de facturation", "Mise en place de tests automatisés"]),
            ],
            school="Université Claude Bernard Lyon 1",
            degree="Master en Informatique",
            study_dates="2015 – 2017",
            skills=["Python", "PostgreSQL", "Docker", "Kubernetes", "Git"],
            certifications=["Certification AWS Cloud Practitioner"],
            headings={"summary": "Profil", "experience": "Expérience professionnelle", "education": "Formation",
                      "skills": "Compétences", "certifications": "Certifications"},
        ),
        Profile(
            name="Thomas Bernard",
            email="thomas.bernard@example.com",
            phone="+33 6 98 76 54 32",
            city="Valence, France",
            summary="Infirmier diplômé d'État, habitué aux services de chirurgie et à l'accompagnement des patients.",
            jobs=[
                ("Infirmier", "Clinique du Parc", "Valence", "janvier 2019 – aujourd'hui",
                 ["Suivi des patients après une opération", "Encadrement des nouveaux infirmiers"]),
                ("Infirmier remplaçant", "Centre Hospitalier Aurore", "Montélimar", "juin 2016 – décembre 2018",
                 ["Distribution des traitements quotidiens", "Tenue des dossiers de soins"]),
            ],
            school="Institut de Formation en Soins Infirmiers de Valence",
            degree="Diplôme d'État d'infirmier",
            study_dates="2013 – 2016",
            skills=["Soins post-opératoires", "Dossiers patients", "Premiers secours", "Hygiène hospitalière", "Communication"],
            certifications=["Attestation de formation aux gestes et soins d'urgence"],
            headings={"summary": "Résumé professionnel", "experience": "Parcours professionnel", "education": "Formation et diplômes",
                      "skills": "Savoir-faire", "certifications": "Formations complémentaires"},
        ),
        Profile(
            name="Léa Moreau",
            email="lea.moreau@example.com",
            phone="+33 7 11 22 33 44",
            city="Strasbourg, France",
            summary="Analyste financière spécialisée dans les prévisions budgétaires et le reporting mensuel.",
            jobs=[
                ("Analyste financière", "Banque Rivage", "Strasbourg", "octobre 2021 – aujourd'hui",
                 ["Préparation des rapports mensuels de trésorerie", "Prévision des flux de trésorerie trimestriels"]),
                ("Assistante comptable", "Cabinet Delmas et Associés", "Mulhouse", "août 2018 – septembre 2021",
                 ["Rapprochement des comptes bancaires", "Suivi des factures fournisseurs"]),
            ],
            school="École de Management de Strasbourg",
            degree="Master en Finance d'entreprise",
            study_dates="2016 – 2018",
            skills=["Excel", "Power BI", "SQL", "Reporting financier", "Prévisions"],
            certifications=["CFA Level II"],
            headings={"summary": "À propos", "experience": "Emplois", "education": "Cursus",
                      "skills": "Outils et méthodes", "certifications": "Distinctions"},
        ),
    ],
    "es": [
        Profile(
            name="Lucía Fernández",
            email="lucia.fernandez@example.com",
            phone="+34 612 345 678",
            city="Madrid, España",
            summary="Ingeniera de software con seis años de experiencia en desarrollo de servicios y automatización.",
            jobs=[
                ("Ingeniera de software senior", "Nexo Sistemas S.L.", "Madrid", "marzo 2020 - actualidad",
                 ["Diseño de servicios para el seguimiento de pedidos", "Automatización de despliegues en la nube"]),
                ("Desarrolladora back-end", "Taller Digital S.A.", "Valencia", "septiembre 2017 - febrero 2020",
                 ["Desarrollo de módulos de facturación", "Implantación de pruebas automáticas"]),
            ],
            school="Universidad Politécnica de Madrid",
            degree="Máster en Ingeniería Informática",
            study_dates="2015 - 2017",
            skills=["Python", "PostgreSQL", "Docker", "Kubernetes", "Git"],
            certifications=["Certificación AWS Cloud Practitioner"],
            headings={"summary": "Perfil profesional", "experience": "Experiencia laboral", "education": "Formación académica",
                      "skills": "Habilidades técnicas", "certifications": "Certificaciones"},
        ),
        Profile(
            name="Javier Ortega",
            email="javier.ortega@example.com",
            phone="+34 655 987 321",
            city="Sevilla, España",
            summary="Enfermero con experiencia en cirugía y en la atención directa a pacientes hospitalizados.",
            jobs=[
                ("Enfermero", "Clínica del Sur", "Sevilla", "enero de 2019 - actualidad",
                 ["Seguimiento de pacientes tras la operación", "Formación de personal de nuevo ingreso"]),
                ("Enfermero suplente", "Hospital Virgen Aurora", "Cádiz", "junio de 2016 - diciembre de 2018",
                 ["Administración de tratamientos diarios", "Registro de historiales clínicos"]),
            ],
            school="Universidad de Sevilla",
            degree="Grado en Enfermería",
            study_dates="2012 - 2016",
            skills=["Cuidados postoperatorios", "Historias clínicas", "Primeros auxilios", "Higiene hospitalaria", "Comunicación"],
            certifications=["Curso de soporte vital avanzado"],
            headings={"summary": "Resumen profesional", "experience": "Trayectoria profesional", "education": "Estudios",
                      "skills": "Conocimientos", "certifications": "Cursos"},
        ),
        Profile(
            name="Marta Ríos",
            email="marta.rios@example.com",
            phone="+34 644 100 200",
            city="Barcelona, España",
            summary="Analista financiera especializada en previsiones presupuestarias e informes mensuales.",
            jobs=[
                ("Analista financiera", "Banco Litoral", "Barcelona", "octubre 2021 - actualidad",
                 ["Preparación de informes mensuales de tesorería", "Previsión trimestral de flujos de caja"]),
                ("Auxiliar contable", "Asesoría Delmas y Asociados", "Girona", "agosto 2018 - septiembre 2021",
                 ["Conciliación de cuentas bancarias", "Control de facturas de proveedores"]),
            ],
            school="Universidad de Barcelona",
            degree="Máster en Finanzas Corporativas",
            study_dates="2016 - 2018",
            skills=["Excel", "Power BI", "SQL", "Informes financieros", "Previsiones"],
            certifications=["CFA Level II"],
            headings={"summary": "Sobre mí", "experience": "Empleos", "education": "Titulación",
                      "skills": "Herramientas y métodos", "certifications": "Logros"},
        ),
    ],
    "de": [
        Profile(
            name="Lena Hoffmann",
            email="lena.hoffmann@example.com",
            phone="+49 151 2345 6789",
            city="München, Deutschland",
            summary="Softwareentwicklerin mit sechs Jahren Erfahrung in Backend-Entwicklung und Cloud-Infrastruktur.",
            jobs=[
                ("Senior Softwareentwicklerin", "Nordlicht Systeme GmbH", "München", "März 2020 – heute",
                 ["Entwurf von Schnittstellen für die Auftragsverfolgung", "Migration der Dienste auf Kubernetes"]),
                ("Backend-Entwicklerin", "Werkstatt Digital GmbH", "Augsburg", "September 2017 – Februar 2020",
                 ["Entwicklung von Abrechnungsmodulen", "Einführung automatisierter Tests"]),
            ],
            school="Technische Universität München",
            degree="Master Informatik",
            study_dates="2015 – 2017",
            skills=["Python", "PostgreSQL", "Docker", "Kubernetes", "Git"],
            certifications=["AWS Cloud Practitioner Zertifikat"],
            headings={"summary": "Profil", "experience": "Berufserfahrung", "education": "Ausbildung",
                      "skills": "Kenntnisse", "certifications": "Zertifikate"},
        ),
        Profile(
            name="Jonas Weber",
            email="jonas.weber@example.com",
            phone="+49 170 9876 5432",
            city="Stuttgart, Deutschland",
            summary="Gesundheits- und Krankenpfleger mit Erfahrung in der Chirurgie und in der Betreuung von Patienten.",
            jobs=[
                ("Gesundheits- und Krankenpfleger", "Klinik am Park", "Stuttgart", "Januar 2019 – heute",
                 ["Betreuung der Patienten nach Operationen", "Anleitung neuer Mitarbeiter"]),
                ("Krankenpfleger", "Kreiskrankenhaus Aurora", "Esslingen", "Juni 2016 – Dezember 2018",
                 ["Verteilung der täglichen Medikation", "Pflege der Patientenakten"]),
            ],
            school="Universität Tübingen",
            degree="Bachelor Pflegewissenschaft",
            study_dates="2012 – 2016",
            skills=["Postoperative Pflege", "Patientenakten", "Erste Hilfe", "Krankenhaushygiene", "Kommunikation"],
            certifications=["Weiterbildung Notfallmanagement"],
            headings={"summary": "Kurzprofil", "experience": "Beruflicher Werdegang", "education": "Studium",
                      "skills": "Fachkenntnisse", "certifications": "Weiterbildung"},
        ),
        Profile(
            name="Clara Fischer",
            email="clara.fischer@example.com",
            phone="+49 160 1122 3344",
            city="Frankfurt, Deutschland",
            summary="Finanzanalystin mit Schwerpunkt auf Budgetplanung und monatlichem Reporting.",
            jobs=[
                ("Finanzanalystin", "Rheinbank AG", "Frankfurt", "Oktober 2021 – heute",
                 ["Erstellung monatlicher Liquiditätsberichte", "Quartalsprognosen für den Cashflow"]),
                ("Buchhalterin", "Delmas und Partner GmbH", "Darmstadt", "August 2018 – September 2021",
                 ["Abstimmung der Bankkonten", "Kontrolle der Lieferantenrechnungen"]),
            ],
            school="Goethe-Universität Frankfurt",
            degree="Master Betriebswirtschaftslehre",
            study_dates="2016 – 2018",
            skills=["Excel", "Power BI", "SQL", "Finanzberichte", "Prognosen"],
            certifications=["CFA Level II"],
            headings={"summary": "Über mich", "experience": "Werdegang", "education": "Akademische Laufbahn",
                      "skills": "Werkzeuge", "certifications": "Auszeichnungen"},
        ),
    ],
    "pt": [
        Profile(
            name="Beatriz Almeida",
            email="beatriz.almeida@example.com",
            phone="+55 11 91234 5678",
            city="São Paulo, Brasil",
            summary="Engenheira de software com seis anos de experiência em desenvolvimento de serviços e infraestrutura em nuvem.",
            jobs=[
                ("Engenheira de software sênior", "Orbita Sistemas Ltda", "São Paulo", "março de 2020 - atualmente",
                 ["Projeto de APIs para o acompanhamento de pedidos", "Migração dos serviços para Kubernetes"]),
                ("Desenvolvedora back-end", "Oficina Digital Ltda", "Campinas", "setembro de 2017 - fevereiro de 2020",
                 ["Desenvolvimento de módulos de faturamento", "Implantação de testes automatizados"]),
            ],
            school="Universidade de São Paulo",
            degree="Mestrado em Ciência da Computação",
            study_dates="2015 - 2017",
            skills=["Python", "PostgreSQL", "Docker", "Kubernetes", "Git"],
            certifications=["Certificação AWS Cloud Practitioner"],
            headings={"summary": "Perfil profissional", "experience": "Experiência profissional", "education": "Formação acadêmica",
                      "skills": "Competências técnicas", "certifications": "Certificações"},
        ),
        Profile(
            name="Rafael Costa",
            email="rafael.costa@example.com",
            phone="+55 21 99876 5432",
            city="Rio de Janeiro, Brasil",
            summary="Enfermeiro com experiência em cirurgia e no acompanhamento direto de pacientes internados.",
            jobs=[
                ("Enfermeiro", "Clínica do Parque", "Rio de Janeiro", "janeiro de 2019 - atualmente",
                 ["Acompanhamento de pacientes após operações", "Treinamento de novos profissionais"]),
                ("Enfermeiro substituto", "Hospital Aurora", "Niterói", "junho de 2016 - dezembro de 2018",
                 ["Administração dos tratamentos diários", "Registro dos prontuários"]),
            ],
            school="Universidade Federal do Rio de Janeiro",
            degree="Bacharelado em Enfermagem",
            study_dates="2012 - 2016",
            skills=["Cuidados pós-operatórios", "Prontuários", "Primeiros socorros", "Higiene hospitalar", "Comunicação"],
            certifications=["Curso de suporte avançado de vida"],
            headings={"summary": "Resumo profissional", "experience": "Histórico profissional", "education": "Formação",
                      "skills": "Conhecimentos", "certifications": "Cursos"},
        ),
        Profile(
            name="Camila Duarte",
            email="camila.duarte@example.com",
            phone="+55 31 98877 6655",
            city="Belo Horizonte, Brasil",
            summary="Analista financeira especializada em previsões orçamentárias e relatórios mensais.",
            jobs=[
                ("Analista financeira", "Banco Litoral S.A.", "Belo Horizonte", "outubro de 2021 - atualmente",
                 ["Preparação de relatórios mensais de tesouraria", "Previsão trimestral do fluxo de caixa"]),
                ("Assistente contábil", "Escritório Delmas e Associados", "Contagem", "agosto de 2018 - setembro de 2021",
                 ["Conciliação das contas bancárias", "Controle das faturas de fornecedores"]),
            ],
            school="Universidade Federal de Minas Gerais",
            degree="Mestrado em Finanças Corporativas",
            study_dates="2016 - 2018",
            skills=["Excel", "Power BI", "SQL", "Relatórios financeiros", "Previsões"],
            certifications=["CFA Level II"],
            headings={"summary": "Sobre mim", "experience": "Trajetória", "education": "Escolaridade",
                      "skills": "Ferramentas e métodos", "certifications": "Conquistas"},
        ),
    ],
    "ru": [
        Profile(
            name="Анна Смирнова",
            email="anna.smirnova@example.com",
            phone="+7 912 345 67 89",
            city="Москва, Россия",
            summary="Инженер-программист с шестью годами опыта в разработке серверной части и облачной инфраструктуры.",
            jobs=[
                ("Ведущий разработчик", "ООО Орбита Системы", "Москва", "март 2020 – по настоящее время",
                 ["Проектирование API для отслеживания заказов", "Перенос сервисов в Kubernetes"]),
                ("Разработчик", "ООО Цифровая Мастерская", "Тверь", "сентябрь 2017 – февраль 2020",
                 ["Разработка модулей выставления счетов", "Внедрение автоматических тестов"]),
            ],
            school="Московский государственный университет",
            degree="Магистр прикладной информатики",
            study_dates="2015 – 2017",
            skills=["Python", "PostgreSQL", "Docker", "Kubernetes", "Git"],
            certifications=["Сертификат AWS Cloud Practitioner"],
            headings={"summary": "О себе", "experience": "Опыт работы", "education": "Образование",
                      "skills": "Навыки", "certifications": "Сертификаты"},
        ),
        Profile(
            name="Дмитрий Козлов",
            email="dmitry.kozlov@example.com",
            phone="+7 925 987 65 43",
            city="Казань, Россия",
            summary="Врач-хирург с опытом работы в стационаре и наблюдения за пациентами после операций.",
            jobs=[
                ("Врач-хирург", "Клиника Парк", "Казань", "январь 2019 – по настоящее время",
                 ["Наблюдение за пациентами после операций", "Обучение новых сотрудников"]),
                ("Ординатор", "Городская больница Аврора", "Набережные Челны", "июнь 2016 – декабрь 2018",
                 ["Назначение ежедневного лечения", "Ведение медицинских карт"]),
            ],
            school="Казанский государственный медицинский университет",
            degree="Специалитет по специальности лечебное дело",
            study_dates="2010 – 2016",
            skills=["Послеоперационный уход", "Медицинские карты", "Первая помощь", "Гигиена", "Коммуникация"],
            certifications=["Курс повышения квалификации по неотложной помощи"],
            headings={"summary": "Профиль", "experience": "Профессиональный опыт", "education": "Обучение",
                      "skills": "Профессиональные навыки", "certifications": "Дополнительное образование"},
        ),
        Profile(
            name="Елена Новикова",
            email="elena.novikova@example.com",
            phone="+7 903 112 23 34",
            city="Санкт-Петербург, Россия",
            summary="Финансовый аналитик, специализируется на бюджетном планировании и ежемесячной отчётности.",
            jobs=[
                ("Финансовый аналитик", "АО Банк Берег", "Санкт-Петербург", "октябрь 2021 – по настоящее время",
                 ["Подготовка ежемесячных отчётов по ликвидности", "Квартальный прогноз денежных потоков"]),
                ("Помощник бухгалтера", "ООО Дельма и Партнёры", "Выборг", "август 2018 – сентябрь 2021",
                 ["Сверка банковских счетов", "Контроль счетов поставщиков"]),
            ],
            school="Санкт-Петербургский государственный экономический университет",
            degree="Магистр экономики",
            study_dates="2016 – 2018",
            skills=["Excel", "Power BI", "SQL", "Финансовая отчётность", "Прогнозирование"],
            certifications=["CFA Level II"],
            headings={"summary": "Цель", "experience": "Карьера", "education": "Учёба",
                      "skills": "Компетенции", "certifications": "Достижения"},
        ),
    ],
}

SECTION_ORDER = ("summary", "experience", "education", "skills", "certifications")


def _body(profile: Profile) -> Dict[str, List[str]]:
    """The lines of every section, in the order they are drawn."""

    experience: List[str] = []

    for role, company, city, dates, bullets in profile.jobs:
        experience += [role, f"{company}, {city}", dates]
        experience += [f"• {bullet}" for bullet in bullets]

    return {
        "personal_info": [profile.name, profile.email, profile.phone, profile.city],
        "summary": [profile.summary],
        "experience": experience,
        "education": [profile.school, profile.degree, profile.study_dates],
        "skills": [", ".join(profile.skills)],
        "certifications": list(profile.certifications),
    }


def _entities(profile: Profile) -> Dict[str, List[str]]:
    return {
        "name": [profile.name],
        "companies": [job[1] for job in profile.jobs],
        "roles": [job[0] for job in profile.jobs],
        "schools": [profile.school],
        "degrees": [profile.degree],
        "skills": list(profile.skills),
        "certifications": list(profile.certifications),
    }


def _draw(path: Path, profile: Profile, fonts: Dict[str, str]) -> None:
    document = fitz.open()
    page = document.new_page()
    register_fonts(page, fonts)

    writer = _Writer(document, page, 72, fonts, allow_new_pages=True)
    body = _body(profile)

    writer.line(body["personal_info"][0], size=16, bold=True)

    for text in body["personal_info"][1:]:
        writer.line(text)

    for section in SECTION_ORDER:
        writer.gap(10)
        writer.line(profile.headings[section].upper(), size=12, bold=True)

        for text in body[section]:
            writer.line(text)

    document.save(str(path))
    document.close()


def build_language_corpus(
    directory: Path,
    languages: Optional[List[str]] = None,
) -> List[LanguageDocument]:
    """Draws the CVs into `directory`; languages without a usable font are skipped."""

    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)

    documents: List[LanguageDocument] = []

    for language in languages or list(LANGUAGES):
        fonts = _font_sources(language)

        if fonts is None:
            continue

        for index, profile in enumerate(PROFILES[language]):
            path = directory / f"{language}_{index}.pdf"
            _draw(path, profile, fonts)

            truth = [
                TruthLine(section, text)
                for section, lines in _body(profile).items()
                for text in lines
            ]

            documents.append(
                LanguageDocument(
                    id=f"{language}-{index}",
                    style="upper",
                    layout="single",
                    language=language,
                    path=path,
                    truth=truth,
                    entities=_entities(profile),
                )
            )

    return documents
