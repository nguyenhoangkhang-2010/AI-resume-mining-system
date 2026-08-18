from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from loguru import logger

from app.core.config.settings import settings


class LLMExtractor:

    def __init__(self) -> None:

        self._provider = (
            getattr(
                settings,
                "LLM_PROVIDER",
                "huggingface",
            )
            or "huggingface"
        ).strip().casefold()

        if self._provider == "llama_cpp":
            self._init_llama_cpp()
        else:
            self._provider = "huggingface"
            self._init_huggingface()

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def _init_huggingface(self) -> None:

        from transformers import (
            AutoModelForCausalLM,
            AutoTokenizer,
            pipeline,
        )

        logger.info(
            "Loading LLM model (huggingface backend): {}",
            settings.LLM_MODEL_NAME,
        )

        self.tokenizer = AutoTokenizer.from_pretrained(
            settings.LLM_MODEL_NAME,
        )

        self.tokenizer.padding_side = "left"

        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        self.model = AutoModelForCausalLM.from_pretrained(
            settings.LLM_MODEL_NAME,
        )

        device = self._resolve_device()

        logger.info(
            "Initializing LLM pipeline on device: {}",
            device,
        )

        self.pipe = pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
            device=device,
            return_full_text=False,
        )

        logger.success(
            "LLM model loaded successfully (huggingface backend).",
        )

    def _init_llama_cpp(self) -> None:

        try:
            from llama_cpp import Llama
        except ImportError as exc:
            logger.error(
                "settings.LLM_PROVIDER is 'llama_cpp' but the "
                "llama-cpp-python package is not installed. Install "
                "it with: pip install llama-cpp-python"
            )
            raise exc

        model_path = settings.LLM_GGUF_MODEL_PATH

        if not os.path.isfile(model_path):
            raise FileNotFoundError(
                f"GGUF model file not found at '{model_path}'. "
                "Check settings.LLM_GGUF_MODEL_PATH."
            )

        threads = self._resolve_gguf_threads()

        logger.info(
            "Loading LLM model (llama_cpp backend): {} "
            "(n_ctx={}, n_threads={}, n_gpu_layers={})",
            model_path,
            settings.LLM_GGUF_CONTEXT_SIZE,
            threads,
            settings.LLM_GGUF_GPU_LAYERS,
        )

        self._llama = Llama(
            model_path=model_path,
            n_ctx=settings.LLM_GGUF_CONTEXT_SIZE,
            n_threads=threads,
            n_gpu_layers=settings.LLM_GGUF_GPU_LAYERS,
            verbose=False,
        )

        logger.success(
            "LLM model loaded successfully (llama_cpp backend).",
        )

    @staticmethod
    def _resolve_gguf_threads() -> int:

        configured = getattr(
            settings,
            "LLM_GGUF_THREADS",
            0,
        )

        if isinstance(configured, int) and configured > 0:
            return configured

        cpu_count = os.cpu_count()

        return cpu_count if cpu_count else 4

    def extract_info(
        self,
        text: str,
        prompt_template: Optional[str] = None,
        max_new_tokens: Optional[int] = None,
    ) -> str:

        if not isinstance(text, str):
            return ""

        text = text.strip()

        if not text:
            return ""

        full_prompt = self._prepare_prompt(
            text=text,
            prompt_template=prompt_template,
        )

        if not full_prompt:
            return ""

        try:
            generated_text = self._generate(
                prompt=full_prompt,
                max_new_tokens=max_new_tokens,
            )

            if not generated_text:
                logger.warning(
                    "LLM returned empty generated text.",
                )

                return ""

            logger.debug(
                "LLM generated {} characters.",
                len(generated_text),
            )

            logger.debug(
                "LLM generated text preview: {}",
                generated_text[:1000],
            )

            return generated_text

        except Exception as exc:
            logger.exception(
                "LLM inference failed: {}",
                exc,
            )
            raise

    @staticmethod
    def _resolve_device() -> int:

        device = getattr(
            settings,
            "LLM_DEVICE",
            -1,
        )

        if isinstance(device, int):
            return device

        if isinstance(device, str):
            normalized = device.strip().casefold()

            if normalized == "cpu":
                return -1

            if normalized.isdigit():
                return int(normalized)

            if normalized.startswith("cuda:"):
                try:
                    return int(
                        normalized.split(
                            ":",
                            1,
                        )[1]
                    )

                except ValueError:
                    logger.warning(
                        "Invalid CUDA device '{}'. "
                        "Falling back to CPU.",
                        device,
                    )

                    return -1

        logger.warning(
            "Unsupported LLM device '{}'. "
            "Falling back to CPU.",
            device,
        )

        return -1

    def _prepare_prompt(
        self,
        text: str,
        prompt_template: Optional[str],
    ) -> str:

        if not text:
            return ""

        if prompt_template and prompt_template.strip():
            prompt = self._build_prompt(
                text=text,
                prompt_template=prompt_template,
            )

        else:
            prompt = text.strip()

            max_chars = getattr(
                settings,
                "LLM_MAX_INPUT_CHARS",
                12000,
            )

            if len(prompt) > max_chars:
                logger.warning(
                    "LLM full prompt truncated from {} to {} characters.",
                    len(prompt),
                    max_chars,
                )

                prompt = prompt[:max_chars]

        return prompt

    def _build_prompt(
        self,
        text: str,
        prompt_template: str,
    ) -> str:

        max_chars = getattr(
            settings,
            "LLM_MAX_INPUT_CHARS",
            12000,
        )

        text = text.strip()

        if len(text) > max_chars:
            logger.warning(
                "LLM input truncated from {} to {} characters.",
                len(text),
                max_chars,
            )

            text = text[:max_chars]

        prompt = (
            f"{prompt_template.strip()}\n\n"
            "--- Input Text ---\n"
            f"{text}\n\n"
            "--- Output ---\n"
        )

        return prompt

    def _generate(
        self,
        prompt: str,
        max_new_tokens: Optional[int],
    ) -> str:

        generation_limit = (
            max_new_tokens
            if max_new_tokens is not None
            else getattr(
                settings,
                "MAX_NEW_TOKENS",
                256,
            )
        )

        logger.debug(
            "Running LLM generation with max_new_tokens={}",
            generation_limit,
        )

        if self._provider == "llama_cpp":
            return self._generate_llama_cpp(
                prompt,
                generation_limit,
            )

        return self._generate_huggingface(
            prompt,
            generation_limit,
        )

    def _generate_huggingface(
        self,
        prompt: str,
        generation_limit: int,
    ) -> str:

        wrapped_prompt = self._apply_chat_template(
            prompt,
        )

        generation_kwargs: Dict[str, Any] = {
            "max_new_tokens": generation_limit,
            "return_full_text": False,
            "do_sample": False,
            "pad_token_id": self.tokenizer.pad_token_id,
            "eos_token_id": self.tokenizer.eos_token_id,
        }

        output = self.pipe(
            wrapped_prompt,
            **generation_kwargs,
        )

        return self._extract_huggingface_text(
            output,
        )

    def _apply_chat_template(
        self,
        prompt: str,
    ) -> str:

        if not prompt:
            return ""

        apply_chat_template = getattr(
            self.tokenizer,
            "apply_chat_template",
            None,
        )

        if not callable(apply_chat_template):
            logger.debug(
                "Tokenizer does not expose apply_chat_template; "
                "using plain prompt.",
            )

            return prompt

        try:
            messages = [
                {
                    "role": "user",
                    "content": prompt,
                }
            ]

            formatted_prompt = apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
            )

            if (
                isinstance(
                    formatted_prompt,
                    str,
                )
                and formatted_prompt.strip()
            ):
                logger.debug(
                    "Using tokenizer chat template for LLM prompt.",
                )

                return formatted_prompt

        except Exception as exc:
            logger.warning(
                "Failed to apply tokenizer chat template: {}. "
                "Falling back to plain prompt.",
                exc,
            )

        return prompt

    @classmethod
    def _extract_huggingface_text(
        cls,
        output: Any,
    ) -> str:

        if not output:
            return ""

        if not isinstance(
            output,
            list,
        ):
            return str(output).strip()

        if not output:
            return ""

        first_output = output[0]

        if not isinstance(
            first_output,
            dict,
        ):
            return str(first_output).strip()

        generated = first_output.get(
            "generated_text",
            "",
        )

        if isinstance(
            generated,
            str,
        ):
            return generated.strip()

        if isinstance(
            generated,
            list,
        ):
            return cls._extract_from_message_output(
                generated,
            )

        if generated is None:
            return ""

        return str(generated).strip()

    @staticmethod
    def _extract_from_message_output(
        messages: List[Dict[str, Any]],
    ) -> str:

        for message in reversed(messages):
            if not isinstance(
                message,
                dict,
            ):
                continue

            if message.get("role") != "assistant":
                continue

            content = message.get(
                "content",
            )

            if isinstance(
                content,
                str,
            ):
                return content.strip()

        for message in reversed(messages):
            if not isinstance(
                message,
                dict,
            ):
                continue

            content = message.get(
                "content",
            )

            if isinstance(
                content,
                str,
            ):
                return content.strip()

        return ""

    def _generate_llama_cpp(
        self,
        prompt: str,
        generation_limit: int,
    ) -> str:

        wrapped_prompt = f"[INST] {prompt} [/INST]"

        response = self._llama(
            wrapped_prompt,
            max_tokens=generation_limit,
            temperature=0.0,
            top_p=1.0,
            stop=[
                "</s>",
                "[INST]",
            ],
            echo=False,
        )

        return self._extract_llama_cpp_text(
            response,
        )

    @staticmethod
    def _extract_llama_cpp_text(
        response: Any,
    ) -> str:

        if not response or not isinstance(
            response,
            dict,
        ):
            return ""

        choices = response.get("choices")

        if not choices or not isinstance(
            choices,
            list,
        ):
            return ""

        first_choice = choices[0]

        if not isinstance(
            first_choice,
            dict,
        ):
            return ""

        text = first_choice.get(
            "text",
            "",
        )

        if isinstance(text, str):
            return text.strip()

        return ""