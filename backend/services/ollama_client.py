"""
Ollama HTTP client — thin wrapper around the Ollama REST API.

Sends a prompt to the local Ollama instance and returns the generated text.
Designed for Qwen3:8B but compatible with any model loaded in Ollama.

Usage:
    from services.ollama_client import generate_text
    result = generate_text("Your prompt here")
"""

import json
import logging
from typing import Optional

import httpx

from config import settings

logger = logging.getLogger(__name__)


async def generate_text(
    prompt: str,
    system: Optional[str] = None,
    model: Optional[str] = None,
    timeout: Optional[int] = None,
) -> str:
    """
    Send a prompt to Ollama and return the generated text.

    :param prompt: The user prompt.
    :param system: Optional system instruction prepended to the prompt.
    :param model: Override model name (defaults to settings.OLLAMA_MODEL).
    :param timeout: HTTP timeout in seconds (defaults to settings.OLLAMA_TIMEOUT).
    :returns: Generated text string.
    :raises RuntimeError: If Ollama is unreachable or returns a non-200 status.
    """
    model = model or settings.OLLAMA_MODEL
    timeout = timeout or settings.OLLAMA_TIMEOUT
    url = f"{settings.OLLAMA_BASE_URL}/api/generate"

    payload: dict = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.2,   # low temperature → more deterministic comparisons
            "top_p": 0.9,
        },
    }
    if system:
        payload["system"] = system

    logger.debug("Sending prompt to Ollama model '%s' at %s", model, url)

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "").strip()

    except httpx.ConnectError as exc:
        raise RuntimeError(
            f"Cannot connect to Ollama at {settings.OLLAMA_BASE_URL}. "
            "Make sure Ollama is running (`ollama serve`) and the model is pulled "
            f"(`ollama pull {model}`)."
        ) from exc

    except httpx.HTTPStatusError as exc:
        raise RuntimeError(
            f"Ollama returned HTTP {exc.response.status_code}: {exc.response.text}"
        ) from exc

    except Exception as exc:
        raise RuntimeError(f"Unexpected error calling Ollama: {exc}") from exc


async def check_ollama_health(model: Optional[str] = None) -> dict:
    """
    Probe Ollama and verify the requested model is available.

    Returns a dict with keys:
        - reachable (bool)
        - model_available (bool)
        - error (str | None)
    """
    model = model or settings.OLLAMA_MODEL
    result = {"reachable": False, "model_available": False, "error": None}

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            # List models endpoint
            resp = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            resp.raise_for_status()
            result["reachable"] = True

            models = resp.json().get("models", [])
            available_names = [m.get("name", "") for m in models]
            # Match on base name in case tag differs (e.g., "qwen3:8b" vs "qwen3:8b-instruct")
            result["model_available"] = any(
                model.split(":")[0] in name for name in available_names
            )

    except Exception as exc:
        result["error"] = str(exc)

    return result
