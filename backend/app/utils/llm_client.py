# backend/app/utils/llm_client.py
import json
import logging
import httpx
import asyncio
from typing import List, Dict
from app.core.config import (
    LLM_PROVIDER,
    GOOGLE_API_KEY,
    GOOGLE_MODEL,
    GOOGLE_URL,
)

logger = logging.getLogger("llm_client")
logger.setLevel(logging.DEBUG)

# Use gemini-2.0-flash-lite which is more reliable
GENERATE_CONTENT_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-lite:generateContent"

async def ask_gemini_with_retry(payload, max_retries=5):
    """
    Wrapper function to retry Gemini API calls with exponential backoff.
    This helps handle free tier rate limits and temporary overloads.
    """
    delay = 1
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            url = f"{GENERATE_CONTENT_URL}?key={GOOGLE_API_KEY}"
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(url, json=payload)
            return resp
        except Exception as e:
            last_exception = e
            if attempt == max_retries - 1:  # Last attempt
                break
            
            logger.warning(f"Gemini API call failed (attempt {attempt + 1}), retrying in {delay}s... Error: {str(e)}")
            await asyncio.sleep(delay)
            delay *= 2  # Exponential backoff
    
    raise Exception(f"Gemini API failed after {max_retries} retries: {str(last_exception)}")

async def call_llm(messages: List[Dict[str, str]], max_output_tokens: int = 4096):
    """
    messages: OpenAI-like list:
      [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]
    """

    if LLM_PROVIDER != "google":
        raise RuntimeError("Only google LLM_PROVIDER currently supported by this client.")

    # Check if API key is provided
    if not GOOGLE_API_KEY or GOOGLE_API_KEY == "":
        raise Exception("Google API key is not set. Please check your backend/.env file.")

    # Build a single prompt text (Gemini often expects a single prompt string)
    # We'll convert messages to a single prompt preserving roles
    prompt_lines = []
    for m in messages:
        role = m.get("role", "user")
        content = m.get("content", "")
        prompt_lines.append(f"[{role}]\n{content}\n")
    prompt_text = "\n".join(prompt_lines)

    # Use the more standard generateContent format
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt_text
                    }
                ]
            }
        ],
        "generationConfig": {
            "maxOutputTokens": 4096,
            "temperature": 0.0,
        }
    }

    url = f"{GENERATE_CONTENT_URL}?key={GOOGLE_API_KEY}"
    logger.debug("POST %s payload=%s", url, json.dumps(payload, indent=2))

    try:
        # Use retry wrapper for Gemini API calls
        resp = await ask_gemini_with_retry(payload)
    except Exception as e:
        raise Exception(f"Failed to connect to Gemini API: {str(e)}")

    # Always log status + body for debugging
    text = resp.text
    logger.debug("LLM status=%s body=%s", resp.status_code, text)

    # Try parsing JSON
    try:
        data = resp.json()
    except Exception as e:
        raise Exception(f"LLM returned non-JSON response (status {resp.status_code}): {text}") from e

    # Handle error responses
    if "error" in data:
        error_msg = data["error"].get("message", "Unknown error")
        error_status = data["error"].get("status", "UNKNOWN")
        
        # Provide more specific error messages
        if "API_KEY_INVALID" in error_msg or "API key not valid" in error_msg:
            raise Exception("Invalid Google API key. Please check your backend/.env file and ensure you have a valid Gemini API key.")
        elif error_status == "PERMISSION_DENIED":
            raise Exception("Permission denied. Please check your API key permissions for the Gemini API.")
        elif "RESOURCE_EXHAUSTED" in error_msg or "Quota exceeded" in error_msg:
            raise Exception("Gemini API quota exceeded. Please try again later or upgrade your plan.")
        else:
            raise Exception(f"Gemini API error: {error_msg}")

    # Correct parsing for Gemini v1beta response formats
    try:
        # Shape 1: content.parts
        if "candidates" in data and data["candidates"]:
            cand = data["candidates"][0]
            
            # Handle case where model reached token limit and returned no text
            if cand.get("finishReason") == "MAX_TOKENS":
                return "Model reached maximum token limit and returned no text. Try reducing the input size."

            # Case A: content is dict
            if isinstance(cand.get("content"), dict):
                # Check if content has parts with text
                parts = cand["content"].get("parts", [])
                if parts and "text" in parts[0]:
                    return parts[0]["text"]
                # If content has role but no parts, it means no text was generated
                elif cand["content"].get("role") == "model":
                    return "Model reached maximum token limit and returned no text. Try reducing the input size."

            # Case B: content is list
            if isinstance(cand.get("content"), list):
                for item in cand["content"]:
                    parts = item.get("parts", [])
                    if parts and "text" in parts[0]:
                        return parts[0]["text"]

    except Exception as e:
        logger.exception("Error parsing Gemini response:", exc_info=e)

    # If no valid format matched:
    raise Exception(
        f"Unrecognized Gemini response. status={resp.status_code} json={json.dumps(data, indent=2)[:3000]}"
    )