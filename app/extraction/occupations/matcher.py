from app.extraction.occupations.repository import OccupationRepository


class OccupationMatcher:

    def __init__(self):
        self.repository = OccupationRepository()

    def find(self, text: str):
        if not text:
            return None

        return self.repository.find(text)