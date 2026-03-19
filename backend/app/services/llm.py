import logging
from typing import AsyncIterator

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.language_models.chat_models import BaseChatModel

from ..core.settings import settings

logger = logging.getLogger(__name__)


def get_llm(temperature: float | None = None) -> BaseChatModel:
    """Return Groq if GROQ_API_KEY is set, otherwise fall back to local Ollama."""
    temp = temperature if temperature is not None else settings.ollama_temperature

    if settings.groq_api_key:
        from langchain_groq import ChatGroq
        return ChatGroq(
            api_key=settings.groq_api_key,
            model=settings.groq_model,
            temperature=temp,
        )

    from langchain_ollama import ChatOllama
    return ChatOllama(
        base_url=settings.ollama_base_url,
        model=settings.ollama_model,
        temperature=temp,
        timeout=settings.ollama_timeout,
    )


def _provider_name() -> str:
    return "groq" if settings.groq_api_key else "ollama"


async def invoke_llm(
    system_prompt: str,
    user_message: str,
    temperature: float | None = None,
) -> str:
    """Non-streaming LLM call. Returns the full response text."""
    llm = get_llm(temperature=temperature)
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message),
    ]
    try:
        response = await llm.ainvoke(messages)
        return response.content
    except Exception as e:
        err = str(e).lower()
        if "connection" in err or "refused" in err:
            provider = _provider_name()
            raise ConnectionError(
                f"Cannot connect to {provider}. "
                + ("Check GROQ_API_KEY." if provider == "groq" else f"Make sure Ollama is running at {settings.ollama_base_url}.")
            ) from e
        raise


async def stream_llm(
    system_prompt: str,
    user_message: str,
    temperature: float | None = None,
) -> AsyncIterator[str]:
    """Streaming LLM call. Yields chunks of text."""
    llm = get_llm(temperature=temperature)
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message),
    ]
    try:
        async for chunk in llm.astream(messages):
            if chunk.content:
                yield chunk.content
    except Exception as e:
        err = str(e).lower()
        if "connection" in err or "refused" in err:
            provider = _provider_name()
            raise ConnectionError(
                f"Cannot connect to {provider}. "
                + ("Check GROQ_API_KEY." if provider == "groq" else f"Make sure Ollama is running at {settings.ollama_base_url}.")
            ) from e
        raise
