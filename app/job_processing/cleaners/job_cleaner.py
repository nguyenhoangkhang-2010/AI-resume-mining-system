import re


class JobCleaner:

    def clean(
        self,
        text: str,
    ) -> str:

        text = text.replace("\r\n", "\n")

        text = re.sub(
            r"\n{3,}",
            "\n\n",
            text,
        )

        return text.strip()