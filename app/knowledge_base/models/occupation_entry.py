from dataclasses import dataclass, field


@dataclass
class OccupationEntry:
    id: str
    name: str
    description: str = ""
    aliases: list[str] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)
    source: str = "onet"