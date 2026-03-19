import time
import logging
from typing import Any

import httpx
from langchain_core.tools import tool

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 30.0


def _build_result(
    response_text: str = "",
    latency_ms: float = 0.0,
    status_code: int = 0,
    error: str = "",
) -> dict[str, Any]:
    return {
        "response_text": response_text,
        "latency_ms": latency_ms,
        "status_code": status_code,
        "error": error,
    }


async def _call_openai_compatible(
    url: str,
    messages: list[dict],
    model: str = "gpt-3.5-turbo",
    timeout: float = DEFAULT_TIMEOUT,
    api_key: str = "",
) -> dict[str, Any]:
    payload = {"model": model, "messages": messages}
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    start = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(url, json=payload, headers=headers)
            latency_ms = (time.monotonic() - start) * 1000
            resp.raise_for_status()
            data = resp.json()
            choices = data.get("choices") or []
            text = (choices[0].get("message") or {}).get("content", "") if choices else ""
            if not isinstance(text, str):
                text = str(text)
            return _build_result(response_text=text, latency_ms=latency_ms, status_code=resp.status_code)
    except httpx.ConnectError:
        latency_ms = (time.monotonic() - start) * 1000
        return _build_result(latency_ms=latency_ms, error=f"Connection refused: {url}")
    except httpx.TimeoutException:
        latency_ms = (time.monotonic() - start) * 1000
        return _build_result(latency_ms=latency_ms, error=f"Timeout after {timeout}s")
    except httpx.HTTPStatusError as e:
        latency_ms = (time.monotonic() - start) * 1000
        return _build_result(latency_ms=latency_ms, status_code=e.response.status_code, error=f"HTTP {e.response.status_code}: {e.response.text[:200]}")
    except Exception as e:
        latency_ms = (time.monotonic() - start) * 1000
        return _build_result(latency_ms=latency_ms, error=str(e))


async def _call_simple_endpoint(
    url: str,
    message: str,
    timeout: float = DEFAULT_TIMEOUT,
) -> dict[str, Any]:
    payload = {"message": message}
    start = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(url, json=payload)
            latency_ms = (time.monotonic() - start) * 1000
            resp.raise_for_status()
            data = resp.json()
            text = data.get("response") or data.get("message") or data.get("text") or str(data)
            return _build_result(response_text=text, latency_ms=latency_ms, status_code=resp.status_code)
    except httpx.ConnectError:
        latency_ms = (time.monotonic() - start) * 1000
        return _build_result(latency_ms=latency_ms, error=f"Connection refused: {url}")
    except httpx.TimeoutException:
        latency_ms = (time.monotonic() - start) * 1000
        return _build_result(latency_ms=latency_ms, error=f"Timeout after {timeout}s")
    except httpx.HTTPStatusError as e:
        latency_ms = (time.monotonic() - start) * 1000
        return _build_result(latency_ms=latency_ms, status_code=e.response.status_code, error=f"HTTP {e.response.status_code}")
    except Exception as e:
        latency_ms = (time.monotonic() - start) * 1000
        return _build_result(latency_ms=latency_ms, error=str(e))


async def _call_ollama(
    url: str,
    model: str,
    message: str,
    timeout: float = DEFAULT_TIMEOUT,
) -> dict[str, Any]:
    # Accept bare base URL (http://localhost:11434) or full path
    if not url.rstrip("/").endswith("/api/chat"):
        url = url.rstrip("/") + "/api/chat"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": message}],
        "stream": False,
    }
    start = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(url, json=payload)
            latency_ms = (time.monotonic() - start) * 1000
            resp.raise_for_status()
            data = resp.json()
            text = data.get("message", {}).get("content", "")
            return _build_result(response_text=text, latency_ms=latency_ms, status_code=resp.status_code)
    except httpx.ConnectError:
        latency_ms = (time.monotonic() - start) * 1000
        return _build_result(latency_ms=latency_ms, error=f"Connection refused: {url}. Is Ollama running?")
    except httpx.TimeoutException:
        latency_ms = (time.monotonic() - start) * 1000
        return _build_result(latency_ms=latency_ms, error=f"Timeout after {timeout}s")
    except httpx.HTTPStatusError as e:
        latency_ms = (time.monotonic() - start) * 1000
        return _build_result(latency_ms=latency_ms, status_code=e.response.status_code, error=f"HTTP {e.response.status_code}: {e.response.text[:200]}")
    except Exception as e:
        latency_ms = (time.monotonic() - start) * 1000
        return _build_result(latency_ms=latency_ms, error=str(e))


# LangChain @tool wrappers — for future use in LLM agent tool-calling
@tool
async def call_openai_compatible(url: str, messages: list[dict], model: str = "gpt-3.5-turbo", timeout: float = DEFAULT_TIMEOUT) -> dict[str, Any]:
    """Call an OpenAI-compatible chat completions endpoint."""
    return await _call_openai_compatible(url, messages, model, timeout)


@tool
async def call_simple_endpoint(url: str, message: str, timeout: float = DEFAULT_TIMEOUT) -> dict[str, Any]:
    """Call a simple endpoint that takes {message: str} and returns {response: str}."""
    return await _call_simple_endpoint(url, message, timeout)


@tool
async def call_ollama(url: str, model: str, message: str, timeout: float = DEFAULT_TIMEOUT) -> dict[str, Any]:
    """Call Ollama's /api/chat endpoint."""
    return await _call_ollama(url, model, message, timeout)


async def call_target(
    target_url: str,
    target_type: str,
    message: str,
    model: str = "",
    timeout: float = DEFAULT_TIMEOUT,
    api_key: str = "",
) -> dict[str, Any]:
    """Dispatch to the appropriate caller based on target type."""
    if target_type == "ollama":
        return await _call_ollama(target_url, model, message, timeout)
    elif target_type == "openai":
        messages = [{"role": "user", "content": message}]
        return await _call_openai_compatible(target_url, messages, model or "gpt-3.5-turbo", timeout, api_key)
    else:
        return await _call_simple_endpoint(target_url, message, timeout)
