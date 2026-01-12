"""LLM model factory for creating chat models."""

import os
from typing import Literal
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseChatModel


def get_llm(
    provider: Literal["openai", "anthropic"] | None = None,
    model: str | None = None,
    temperature: float = 0.0,
) -> BaseChatModel:
    """
    Factory function to create an LLM instance.
    
    Args:
        provider: LLM provider ("openai" or "anthropic")
        model: Model name (e.g., "gpt-4o", "claude-3-5-sonnet-20241022")
        temperature: Temperature for generation (default: 0.0 for deterministic)
    
    Returns:
        BaseChatModel instance
    """
    provider = provider or os.getenv("DEFAULT_LLM_PROVIDER", "openai")
    
    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        model = model or os.getenv("DEFAULT_MODEL", "gpt-4o")
        return ChatOpenAI(model=model, temperature=temperature, api_key=api_key)
    
    elif provider == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
        model = model or os.getenv("DEFAULT_MODEL", "claude-3-5-sonnet-20241022")
        return ChatAnthropic(model=model, temperature=temperature, api_key=api_key)
    
    else:
        raise ValueError(f"Unknown provider: {provider}")

