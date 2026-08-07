from enum import Enum


class EntityType(str, Enum):

    PERSON = "PERSON"

    COMPANY = "COMPANY"

    OCCUPATION = "OCCUPATION"

    SKILL = "SKILL"

    CERTIFICATION = "CERTIFICATION"

    EDUCATION = "EDUCATION"

    UNKNOWN = "UNKNOWN"