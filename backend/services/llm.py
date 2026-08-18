"""Gemini LLM service — wraps the Google Generative AI SDK.

Uses gemini-3.6-flash (free tier) for fast, cost-effective extraction.
Falls back to mock mode gracefully if the API key is missing or calls fail.
"""
import json
import logging
from typing import Optional

from backend.config import settings

logger = logging.getLogger(__name__)

_model = None


def _get_model():
    """Lazy-init the Gemini model client."""
    global _model
    if _model is not None:
        return _model

    try:
        import google.generativeai as genai
        genai.configure(api_key=settings.google_api_key)
        _model = genai.GenerativeModel(
            model_name=settings.gemini_model,
            generation_config={
                "temperature": 0.1,  # Low temp for deterministic extraction
                "top_p": 0.95,
                "max_output_tokens": 4096,
                "response_mime_type": "application/json",
            },
        )
        logger.info(f"Gemini model initialized: {settings.gemini_model}")
        return _model
    except Exception as e:
        logger.error(f"Failed to initialize Gemini: {e}")
        return None


async def call_gemini(system_prompt: str, user_prompt: str) -> Optional[str]:
    """Call Gemini Flash and return the response text.
    
    Returns None on failure (caller should fall back to mock).
    Never raises — graceful degradation per assessment requirements.
    """
    if settings.mock_llm:
        return None

    if not settings.google_api_key:
        logger.warning("GOOGLE_API_KEY not set, falling back to mock extraction")
        return None

    model = _get_model()
    if model is None:
        return None

    try:
        # Gemini uses a chat-like interface — combine system + user as prompt
        full_prompt = f"{system_prompt}\n\n---\n\n{user_prompt}"
        response = await model.generate_content_async(full_prompt)

        if response and response.text:
            return response.text
        else:
            logger.warning("Gemini returned empty response")
            return None

    except Exception as e:
        logger.error(f"Gemini API call failed: {type(e).__name__}: {e}")
        return None


def parse_json_response(text: str) -> list:
    """Safely parse a JSON array from Gemini's response."""
    if not text:
        return []

    try:
        # Try direct parse
        result = json.loads(text)
        if isinstance(result, list):
            return result
        if isinstance(result, dict) and "items" in result:
            return result["items"]
        if isinstance(result, dict) and "facts" in result:
            return result["facts"]
        if isinstance(result, dict) and "findings" in result:
            return result["findings"]
        if isinstance(result, dict) and "conflicts" in result:
            return result["conflicts"]
        return [result]
    except json.JSONDecodeError:
        # Try to extract JSON array from markdown code blocks
        import re
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        logger.warning(f"Could not parse Gemini response as JSON: {text[:200]}")
        return []
