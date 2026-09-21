"""Provider-agnostic LLM wrapper. Works with any OpenAI-compatible API
(Groq, OpenRouter, Ollama, ...). Change provider by editing .env, not code.
Adds token pacing (to respect free-tier limits) and usage tracking."""
import logging
import os
import time
from collections import deque

import requests
from dotenv import load_dotenv

load_dotenv()
log = logging.getLogger(__name__)

BASE_URL = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")
MODEL = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")
API_KEY = os.getenv("LLM_API_KEY", "")
# Groq's free tier allows 8,000 tokens/minute on this model; stay safely under it.
TPM_BUDGET = int(os.getenv("LLM_TPM_BUDGET", "7000"))
REASONING_EFFORT = os.getenv("LLM_REASONING_EFFORT", "low" if "gpt-oss" in MODEL else "")

usage_totals = {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0}
_recent = deque()  # (time, tokens) for calls made in the last minute


class LLMError(Exception):
    pass


def _used_last_minute():
    cutoff = time.monotonic() - 60
    while _recent and _recent[0][0] < cutoff:
        _recent.popleft()
    return sum(tokens for _, tokens in _recent)


def _pace(needed):
    """Waits until `needed` more tokens fit inside the per-minute budget."""
    while True:
        used = _used_last_minute()
        if not _recent or used + needed <= TPM_BUDGET:
            return
        wait = max(_recent[0][0] + 60 - time.monotonic(), 0) + 1
        log.info("Pacing: waiting %.0fs to stay under the token limit", wait)
        time.sleep(wait)


def _wait_seconds(response, attempt):
    try:
        return min(float(response.headers.get("retry-after", "")), 60)
    except ValueError:
        return 2 ** (attempt + 1)


def complete(messages, json_mode=False, temperature=0.2, max_tokens=2000, max_retries=3, timeout=90):
    """Returns the model's reply text. Paces calls and retries rate limits and server errors."""
    if not API_KEY:
        raise LLMError("LLM_API_KEY is not set (check your .env file)")
    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    if REASONING_EFFORT:
        payload["reasoning_effort"] = REASONING_EFFORT
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    needed = sum(len(m["content"]) for m in messages) // 3 + max_tokens  # conservative estimate

    last_error = None
    for attempt in range(max_retries + 1):
        _pace(needed)
        wait = 2 ** (attempt + 1)
        try:
            response = requests.post(
                f"{BASE_URL}/chat/completions", json=payload, headers=headers, timeout=timeout
            )
        except requests.RequestException as e:
            last_error = type(e).__name__
        else:
            status = response.status_code
            if status == 429 or status >= 500:
                last_error = f"HTTP {status}"
                wait = _wait_seconds(response, attempt)
            elif status == 400 and "reasoning_effort" in payload and "reasoning" in response.text.lower():
                log.warning("Provider rejected reasoning_effort; retrying without it")
                payload.pop("reasoning_effort")
                last_error = "HTTP 400 (reasoning_effort)"
                wait = 0
            elif status >= 400:
                raise LLMError(f"HTTP {status}: {response.text[:200]}")
            else:
                try:
                    data = response.json()
                    text = data["choices"][0]["message"]["content"]
                except (KeyError, IndexError, ValueError) as e:
                    raise LLMError("Unexpected response format") from e
                usage = data.get("usage") or {}
                _recent.append((time.monotonic(), usage.get("total_tokens") or needed))
                usage_totals["calls"] += 1
                usage_totals["prompt_tokens"] += usage.get("prompt_tokens", 0)
                usage_totals["completion_tokens"] += usage.get("completion_tokens", 0)
                if not text:
                    raise LLMError("Empty reply (the model may have used up max_tokens thinking)")
                return text
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
    print(usage_totals)