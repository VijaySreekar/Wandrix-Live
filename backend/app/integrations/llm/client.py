from langchain_openai import ChatOpenAI
from openai import OpenAI

from app.core.config import get_settings


def create_openai_client() -> OpenAI:
    settings = get_settings()
    return OpenAI(
        api_key=settings.codex_lb_api_key,
        base_url=settings.codex_lb_base_url,
    )


def create_chat_model(*, temperature: float = 0.2) -> ChatOpenAI:
    settings = get_settings()
    return ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.codex_lb_api_key,
        base_url=settings.codex_lb_base_url,
        temperature=temperature,
    )
