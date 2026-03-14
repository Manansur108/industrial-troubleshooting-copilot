"""
Pluggable LLM provider system.

Supports Ollama (default, free local inference) and OpenAI (optional cloud API).
Providers are hot-swappable at runtime via the /api/llm-config endpoint.
"""
from __future__ import annotations

import json
import logging
import re
from abc import ABC, abstractmethod
from typing import Any

import httpx

from app.backend.app.core.config import (
    LLM_PROVIDER,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    OPENAI_API_KEY,
    OPENAI_MODEL,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Runtime config (hot-swappable via API)
# ---------------------------------------------------------------------------
class _RuntimeLLMConfig:
    """Mutable singleton that holds the active LLM configuration."""

    def __init__(self) -> None:
        self.provider: str = LLM_PROVIDER
        self.ollama_base_url: str = OLLAMA_BASE_URL
        self.ollama_model: str = OLLAMA_MODEL
        self.openai_api_key: str = OPENAI_API_KEY
        self.openai_model: str = OPENAI_MODEL

    def to_dict(self) -> dict[str, str]:
        return {
            "provider": self.provider,
            "ollama_base_url": self.ollama_base_url,
            "ollama_model": self.ollama_model,
            "openai_model": self.openai_model,
            "openai_configured": bool(self.openai_api_key),
        }

    def update(self, **kwargs: str) -> None:
        for key, value in kwargs.items():
            if hasattr(self, key) and value is not None:
                setattr(self, key, value)


runtime_config = _RuntimeLLMConfig()


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------
class LLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        """Generate a completion from the LLM. Returns raw text."""

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is reachable."""


# ---------------------------------------------------------------------------
# Ollama provider
# ---------------------------------------------------------------------------
class OllamaProvider(LLMProvider):
    def __init__(self, base_url: str, model: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        payload: dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.3, "num_predict": 2048},
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            with httpx.Client(timeout=120.0) as client:
                resp = client.post(f"{self.base_url}/api/generate", json=payload)
                resp.raise_for_status()
                return resp.json().get("response", "")
        except Exception as exc:
            logger.error("Ollama generate failed: %s", exc)
            raise

    def is_available(self) -> bool:
        try:
            with httpx.Client(timeout=5.0) as client:
                resp = client.get(f"{self.base_url}/api/tags")
                return resp.status_code == 200
        except Exception:
            return False

    def list_models(self) -> list[dict[str, Any]]:
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(f"{self.base_url}/api/tags")
                resp.raise_for_status()
                models = resp.json().get("models", [])
                return [
                    {
                        "name": m["name"],
                        "size": m.get("size", 0),
                        "modified_at": m.get("modified_at", ""),
                    }
                    for m in models
                ]
        except Exception:
            return []


# ---------------------------------------------------------------------------
# OpenAI provider
# ---------------------------------------------------------------------------
class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo") -> None:
        self.api_key = api_key
        self.model = model

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            with httpx.Client(timeout=60.0) as client:
                resp = client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": messages,
                        "temperature": 0.3,
                        "max_tokens": 2048,
                    },
                )
                resp.raise_for_status()
                return resp.json()["choices"][0]["message"]["content"]
        except Exception as exc:
            logger.error("OpenAI generate failed: %s", exc)
            raise

    def is_available(self) -> bool:
        return bool(self.api_key)


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------
def get_provider() -> LLMProvider:
    """Return the currently configured LLM provider."""
    cfg = runtime_config
    if cfg.provider == "openai" and cfg.openai_api_key:
        return OpenAIProvider(api_key=cfg.openai_api_key, model=cfg.openai_model)
    return OllamaProvider(base_url=cfg.ollama_base_url, model=cfg.ollama_model)


def get_ollama_provider() -> OllamaProvider:
    """Return an OllamaProvider for model listing etc."""
    cfg = runtime_config
    return OllamaProvider(base_url=cfg.ollama_base_url, model=cfg.ollama_model)


# ---------------------------------------------------------------------------
# JSON parsing helper
# ---------------------------------------------------------------------------
def parse_json_response(text: str) -> dict[str, Any]:
    """Extract JSON object from LLM response text (handles markdown fences)."""
    # Try to find JSON in code fences first
    fence_match = re.search(r"```(?:json)?\s*\n?(.*?)```", text, re.DOTALL)
    if fence_match:
        text = fence_match.group(1).strip()

    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to find any JSON object
    brace_match = re.search(r"\{.*\}", text, re.DOTALL)
    if brace_match:
        try:
            return json.loads(brace_match.group())
        except json.JSONDecodeError:
            pass

    return {}
