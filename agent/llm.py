"""Provider-agnostic LLM wrapper. Works with any OpenAI-compatible API
(Groq, OpenRouter, Ollama, ...). Change provider by editing .env, not code."""
import logging
import os
import time

import requests
from dotenv import load_dotenv

load_dotenv()
log = logging.getLogger(__name__)

BASE_URL = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")
MODEL = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")
API_KEY = os.getenv("LLM_API_KEY", "")


class LLMError(Exception):
    pass


def _wait_seconds(response, attempt):
    try:
        return min(float(response.headers.get("retry-after", "")), 60)
    except ValueError:
        return 2 ** (attempt + 1)


def complete(messages, json_mode=False, temperature=0.2, max_retries=3, timeout=60):
    """Returns the model's reply text. Retries rate limits and server errors."""
    if not API_KEY:
        raise LLMError("LLM_API_KEY is not set (check your .env file)")
    payload = {"model": MODEL, "messages": messages, "temperature": temperature}
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

    last_error = None
    for attempt in range(max_retries + 1):
        wait = 2 ** (attempt + 1)
        try:
            response = requests.post(
                f"{BASE_URL}/chat/completions", json=payload, headers=headers, timeout=timeout
            )
        except requests.RequestException as e:
            last_error = type(e).__name__
        else:
            if response.status_code == 429 or response.status_code >= 500:
                last_error = f"HTTP {response.status_code}"
                wait = _wait_seconds(response, attempt)
            elif response.status_code >= 400:
                raise LLMError(f"HTTP {response.status_code}: {response.text[:200]}")
            else:
                try:
                    return response.json()["choices"][0]["message"]["content"]
                except (KeyError, IndexError, ValueError) as e:
                    raise LLMError("Unexpected response format") from e
        if attempt < max_retries:
            log.warning("LLM call failed (%s), retrying in %.0fs", last_error, wait)
            time.sleep(wait)
    raise LLMError(f"Failed after {max_retries + 1} attempts: {last_error}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    print(complete([{"role": "user", "content": "Reply with exactly: Jumbo online"}]))
    print(
        complete(
            [{"role": "user", "content": 'Return JSON with keys "status" and "note". status must be "ok".'}],
            json_mode=True,
        )
    )