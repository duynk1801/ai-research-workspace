import json
import re
import logging
from openai import OpenAI
from src.config import MIMO_API_KEY, MIMO_BASE_URL, MIMO_MODEL, DEFAULT_TEMPERATURE, DEFAULT_MAX_TOKENS

logger = logging.getLogger(__name__)

client = OpenAI(
    api_key=MIMO_API_KEY,
    base_url=MIMO_BASE_URL
)


def chat(messages: list[dict], temperature: float = DEFAULT_TEMPERATURE, max_tokens: int = DEFAULT_MAX_TOKENS) -> str:
    completion = client.chat.completions.create(
        model=MIMO_MODEL,
        messages=messages,
        temperature=temperature,
        max_completion_tokens=max_tokens,
        stream=False
    )
    return completion.choices[0].message.content


def _try_parse_json(text: str) -> dict | None:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def _extract_json_from_text(text: str) -> dict | None:
    patterns = [
        r'```json\s*\n(.*?)\n\s*```',
        r'```\s*\n(.*?)\n\s*```',
        r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}',
        r'\[.*?\]',
    ]
    for pattern in patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        for match in matches:
            result = _try_parse_json(match)
            if result is not None:
                return result
    return None


def chat_json(messages: list[dict], temperature: float = DEFAULT_TEMPERATURE, max_tokens: int = DEFAULT_MAX_TOKENS) -> dict:
    for attempt in range(2):
        response = chat(messages, temperature, max_tokens)

        result = _extract_json_from_text(response)
        if result is not None:
            return result

        start = response.find("{")
        end = response.rfind("}") + 1
        if start != -1 and end > start:
            result = _try_parse_json(response[start:end])
            if result is not None:
                return result

        if attempt == 0:
            logger.warning(f"Failed to parse JSON on first attempt, retrying...")
            messages = messages.copy()
            messages.append({"role": "user", "content": "Please respond with valid JSON only. No markdown, no extra text."})

    logger.error(f"Failed to parse JSON from LLM response: {response[:200]}")
    return {"raw": response, "parse_error": True}
