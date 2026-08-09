import re


class EmailExtractor:

    EMAIL_PATTERN = re.compile(
        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    )


    def extract(self, text:str):

        match = self.EMAIL_PATTERN.search(text)

        if not match:
            return None

        return match.group(0)