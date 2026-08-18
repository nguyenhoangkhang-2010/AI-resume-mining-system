from huggingface_hub import login

from app.core.config.settings import settings


def login_huggingface():

    if settings.hf_token:

        login(
            token=settings.hf_token,
            add_to_git_credential=False
        )