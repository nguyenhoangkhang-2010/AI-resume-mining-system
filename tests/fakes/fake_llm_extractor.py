import json


class FakeLLMExtractor:
    """
    Stand-in for LLMExtractor that returns a canned response
    instead of running a real model.
    """

    def __init__(self, response=""):
        self.response = (
            json.dumps(response)
            if isinstance(response, (dict, list))
            else response
        )
        self.calls = []

    def extract_info(
        self,
        text,
        prompt_template=None,
        max_new_tokens=None,
    ):
        self.calls.append(text)
        return self.response
