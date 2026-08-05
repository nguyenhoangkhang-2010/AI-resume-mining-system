from pydantic import BaseModel
from typing import List


class TaxonomyEntry(BaseModel):
    id: str
    name: str
    category: str
    aliases: List[str] = []