from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[3]
load_dotenv(BASE_DIR / '.env')

# --- File Storage ---
UPLOAD_DIR = Path(os.getenv('UPLOAD_DIR', BASE_DIR / 'data' / 'uploads'))
PROCESSED_DIR = Path(os.getenv('PROCESSED_DIR', BASE_DIR / 'data' / 'processed'))
CHROMA_DIR = Path(os.getenv('CHROMA_DIR', BASE_DIR / 'data' / 'chroma'))

# --- LLM Provider ---
LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'ollama')          # "ollama" | "openai"
OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'qwen3:8b')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')

APP_NAME = 'Industrial Troubleshooting Copilot API'

for path in [UPLOAD_DIR, PROCESSED_DIR, CHROMA_DIR]:
    path.mkdir(parents=True, exist_ok=True)
