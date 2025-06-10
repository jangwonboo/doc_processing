"""Configuration settings for the Gemini API summarization script."""
import os
from pathlib import Path

# Gemini API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# API Configuration
MODEL_NAME = "gemini-2.5-flash-preview-05-20"
RATE_LIMIT_REQUESTS_PER_MINUTE = 30  # Reduced for stability
MIN_INTERVAL_BETWEEN_REQUESTS = 2.0  # Increased minimum interval between requests

# Timeout settings (in seconds)
CONNECTION_TIMEOUT = 45.0
READ_TIMEOUT = 1200.0  # Increased to 10 minutes
STREAM_READ_TIMEOUT = 600.0  # Separate timeout for streaming

# Retry settings
MAX_RETRIES = 5  # Increased max retry attempts
INITIAL_RETRY_DELAY = 5.0
MAX_RETRY_DELAY = 60.0
RETRY_MULTIPLIER = 2.0

# Token limits
MAX_INPUT_TOKENS = 1048576  # 1,048,576 tokens
MAX_OUTPUT_TOKENS = 65535    # 65,535 tokens

# Generation configuration
GENERATION_CONFIG = {
    "temperature": 0.2,  # Slightly higher for better creativity
    "max_output_tokens": MAX_OUTPUT_TOKENS,  # Set to model's maximum output tokens
    "top_p": 0.9,  # Slightly lower for more focused responses
    "top_k": 40,
    "response_mime_type": "text/plain"  # Ensure text output
}

PROMPT_FILE = Path("prompt/newneek_prompt.txt")
