"""Stores configuration and environment settings."""

import os
from dotenv import load_dotenv

load_dotenv()

LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "google")

# Google Gemini configuration
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
GOOGLE_MODEL = os.environ.get("GOOGLE_MODEL", "gemini-2.5-flash")  # Use gemini-2.5-flash which is available
GOOGLE_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GOOGLE_MODEL}:generateContent"