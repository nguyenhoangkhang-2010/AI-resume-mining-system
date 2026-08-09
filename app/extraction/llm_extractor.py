import json
from loguru import logger
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM

from app.core.config.settings import settings


class LLMExtractor:
    def __init__(self):
        logger.info(f"Loading LLM model: {settings.LLM_MODEL_NAME}")
        self.tokenizer = AutoTokenizer.from_pretrained(settings.LLM_MODEL_NAME)
        self.model = AutoModelForCausalLM.from_pretrained(settings.LLM_MODEL_NAME)
        self.pipe = pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
            max_new_tokens=settings.MAX_NEW_TOKENS,
        )
        logger.success("LLM model loaded successfully.")

    def extract_info(self, text: str, prompt_template: str) -> str:
        full_prompt = f"{prompt_template}\n\n--- Resume Text ---\n{text}"
        messages = [{"role": "user", "content": full_prompt}]
        
        try:
            output = self.pipe(messages)
            # Extract the generated text which is inside the 'generated_text' key
            # and then get the content part of the assistant's response.
            response_content = output[0]['generated_text'][-1]['content']
            return response_content
        except Exception as e:
            logger.error(f"Error during LLM inference: {e}")
            raise
