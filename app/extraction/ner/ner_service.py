from typing import List, Dict

import spacy


class NERService:

    def __init__(
        self,
        model_name: str = "en_core_web_sm",
    ):
        self.nlp = spacy.load(model_name)

    def extract(
        self,
        text: str,
    ) -> List[Dict[str, str]]:

        if not text:
            return []

        doc = self.nlp(text)

        return [
            {
                "text": entity.text,
                "label": entity.label_,
                "start": entity.start_char,
                "end": entity.end_char,
            }
            for entity in doc.ents
        ]