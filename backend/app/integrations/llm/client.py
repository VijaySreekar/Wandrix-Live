from langchain_openai import ChatOpenAI
from openai import OpenAI

from app.core.config import get_settings


def create_openai_client() -> OpenAI:
    settings = get_settings()
    return OpenAI(
        api_key=settings.codex_lb_api_key,
        base_url=settings.codex_lb_base_url,
    )


def create_chat_model(
    *,
    temperature: float = 0.2,
    timeout: float | None = None,
    max_retries: int | None = None,
) -> ChatOpenAI:
    settings = get_settings()
    return ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.codex_lb_api_key,
        base_url=settings.codex_lb_base_url,
        temperature=temperature,
        timeout=timeout,
        max_retries=max_retries,
    )


def create_quick_plan_chat_model(
    *,
    temperature: float = 0.2,
    timeout: float | None = None,
    max_retries: int | None = None,
    reasoning_effort: str | None = None,
) -> ChatOpenAI:
    settings = get_settings()
    return ChatOpenAI(
        model=settings.quick_plan_model,
        api_key=settings.codex_lb_api_key,
        base_url=settings.codex_lb_base_url,
        temperature=temperature,
        timeout=timeout,
        max_retries=max_retries,
        reasoning_effort=reasoning_effort or settings.quick_plan_reasoning_effort,
    )
