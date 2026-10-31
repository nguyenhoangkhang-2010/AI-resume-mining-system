import threading
from collections import OrderedDict
from types import SimpleNamespace

import pytest

from app.extraction.llm.llm_extractor import INPUT_MARKER, LLMExtractor
from app.extraction.llm.prefix_cache import PrefixCache

INSTRUCTIONS_A = "You extract experience. Be careful and precise." * 3
INSTRUCTIONS_B = "You extract education. Return JSON only." * 3


class FakeLlama:
    """One token per character plus a start token; counts what is read."""

    def __init__(self):
        self._input_ids = []
        self.n_tokens = 0
        self.read = 0
        self.calls = 0
        self.saved = 0
        self.loaded = 0

    def tokenize(self, data, add_bos=True, special=False):
        return ([1] if add_bos else []) + [10 + b for b in data]

    def reset(self):
        self._input_ids, self.n_tokens = [], 0

    def eval(self, tokens):
        self.read += len(tokens)
        self._input_ids = list(self._input_ids[: self.n_tokens]) + list(tokens)
        self.n_tokens = len(self._input_ids)

    def save_state(self):
        self.saved += 1

        return SimpleNamespace(
            ids=list(self._input_ids[: self.n_tokens]),
            llama_state_size=len(self._input_ids) * 1000,
        )

    def load_state(self, state):
        self.loaded += 1
        self._input_ids = list(state.ids)
        self.n_tokens = len(state.ids)

    def __call__(self, prompt, **kwargs):
        self.calls += 1
        tokens = self.tokenize(prompt.encode("utf-8"))
        shared = 0

        for a, b in zip(self._input_ids[: self.n_tokens], tokens):
            if a != b:
                break

            shared += 1

        self.read += len(tokens) - shared
        self._input_ids, self.n_tokens = list(tokens), len(tokens)

        return {"choices": [{"text": f"answer:{len(prompt)}"}]}


def make(prefix_mb=1, results=0, llama=None):
    extractor = LLMExtractor.__new__(LLMExtractor)
    extractor._provider = "llama_cpp"
    extractor._lock = threading.RLock()
    extractor._results = OrderedDict()
    extractor._result_limit = results
    extractor._prefixes = PrefixCache(prefix_mb * 1024 * 1024) if prefix_mb else None
    extractor._llama = llama or FakeLlama()

    return extractor


def ask(extractor, instructions, resume):
    return extractor.extract_info(resume, instructions, max_new_tokens=8)


def prompt_length(instructions, resume):
    return len(instructions.strip()) + len("\n\n") + len(INPUT_MARKER) + len(
        resume.strip()
    ) + len("\n\n--- Output ---\n") + len("[INST]  [/INST]")


# ----------------------------------------------------------- instruction reuse


def test_the_instructions_are_read_once_for_many_resumes():
    extractor = make()
    llama = extractor._llama

    ask(extractor, INSTRUCTIONS_A, "resume one")
    first = llama.read

    ask(extractor, INSTRUCTIONS_A, "resume two!")
    second = llama.read - first

    assert second < len(INSTRUCTIONS_A.strip())
    assert second < first / 2


def test_interleaved_prompts_each_keep_their_instructions():
    extractor = make()
    llama = extractor._llama

    ask(extractor, INSTRUCTIONS_A, "resume one")
    ask(extractor, INSTRUCTIONS_B, "resume one")
    before = llama.read

    ask(extractor, INSTRUCTIONS_A, "resume two")

    assert llama.read - before < len(INSTRUCTIONS_A.strip())
    assert llama.loaded >= 1


def test_the_answer_is_the_same_with_and_without_reuse():
    cached = make()
    plain = make(prefix_mb=0)

    for resume in ("alpha", "beta beta", "gamma"):
        assert ask(cached, INSTRUCTIONS_A, resume) == ask(plain, INSTRUCTIONS_A, resume)


def test_without_the_cache_every_call_reads_everything():
    extractor = make(prefix_mb=0)
    llama = extractor._llama

    ask(extractor, INSTRUCTIONS_A, "resume one")
    ask(extractor, INSTRUCTIONS_B, "resume one")
    before = llama.read

    ask(extractor, INSTRUCTIONS_A, "resume two")

    assert llama.read - before > len(INSTRUCTIONS_A.strip())


def test_a_prompt_without_the_marker_is_left_alone():
    extractor = make()
    extractor._prefixes = PrefixCache(1 << 20)

    extractor._reuse_instructions("[INST] free text [/INST]")

    assert len(extractor._prefixes) == 0
    assert extractor._llama.saved == 0


def test_tokens_that_do_not_start_with_the_instructions_are_not_cached():
    class MergingLlama(FakeLlama):
        # Tokenises the full prompt differently from its first part.
        def tokenize(self, data, add_bos=True, special=False):
            tokens = super().tokenize(data, add_bos, special)

            return [7, *tokens[1:]] if b"merged" in data else tokens

    llama = MergingLlama()
    cache = PrefixCache(1 << 20)

    assert cache.prepare(llama, "abc\n", "abc\nresume") is True
    assert cache.prepare(llama, "abc\n", "abc\nmerged") is False


def test_the_cache_drops_the_oldest_prompt_when_full():
    llama = FakeLlama()
    cache = PrefixCache(capacity_bytes=60_000)

    for number in range(5):
        text = f"{'x' * 20}{number}\n"
        cache.prepare(llama, text, text + "resume")

    assert 1 <= len(cache) < 5
    assert cache.size <= 60_000 + 25_000


def test_a_failing_cache_falls_back_to_reading_the_whole_prompt():
    class Broken(FakeLlama):
        def save_state(self):
            raise RuntimeError("no state")

    extractor = make(llama=Broken())

    assert ask(extractor, INSTRUCTIONS_A, "resume").startswith("answer:")
    assert extractor._prefixes is None


# ---------------------------------------------------------- remembered answers


def test_the_same_prompt_is_not_run_twice():
    extractor = make(results=8)
    llama = extractor._llama

    first = ask(extractor, INSTRUCTIONS_A, "resume one")
    second = ask(extractor, INSTRUCTIONS_A, "resume one")

    assert first == second
    assert llama.calls == 1


def test_a_different_token_limit_is_a_different_prompt():
    extractor = make(results=8)

    extractor.extract_info("resume", INSTRUCTIONS_A, max_new_tokens=8)
    extractor.extract_info("resume", INSTRUCTIONS_A, max_new_tokens=16)

    assert extractor._llama.calls == 2


def test_remembered_answers_are_limited_and_oldest_first():
    extractor = make(results=2)
    llama = extractor._llama

    for name in ("one", "two", "three"):
        ask(extractor, INSTRUCTIONS_A, name)

    ask(extractor, INSTRUCTIONS_A, "three")
    assert llama.calls == 3

    ask(extractor, INSTRUCTIONS_A, "one")
    assert llama.calls == 4


def test_nothing_is_remembered_when_switched_off():
    extractor = make(results=0)

    ask(extractor, INSTRUCTIONS_A, "resume")
    ask(extractor, INSTRUCTIONS_A, "resume")

    assert extractor._llama.calls == 2


def test_empty_answers_are_not_remembered():
    class Silent(FakeLlama):
        def __call__(self, prompt, **kwargs):
            self.calls += 1

            return {"choices": [{"text": ""}]}

    extractor = make(results=8, llama=Silent())

    ask(extractor, INSTRUCTIONS_A, "resume")
    ask(extractor, INSTRUCTIONS_A, "resume")

    assert extractor._llama.calls == 2


@pytest.mark.parametrize("workers", [4])
def test_concurrent_calls_do_not_overlap_in_the_model(workers):
    active = {"now": 0, "max": 0}

    class Watching(FakeLlama):
        def __call__(self, prompt, **kwargs):
            active["now"] += 1
            active["max"] = max(active["max"], active["now"])
            threading.Event().wait(0.01)
            result = super().__call__(prompt, **kwargs)
            active["now"] -= 1

            return result

    extractor = make(llama=Watching())
    threads = [
        threading.Thread(target=ask, args=(extractor, INSTRUCTIONS_A, f"resume {n}"))
        for n in range(workers)
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    assert active["max"] == 1
