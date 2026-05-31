import os

import httpx


class LLMProviderError(Exception):
    pass


def _extract_openai_text(payload: dict) -> str:
    choices = payload.get("choices", [])
    if not choices:
        raise LLMProviderError("No completion choices in provider response.")

    message = choices[0].get("message", {})
    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise LLMProviderError("Provider returned empty message content.")
    return content


def _call_openai_compatible(
    *, api_base: str, api_key: str, model: str, prompt: str
) -> str:
    with httpx.Client(timeout=45.0) as client:
        response = client.post(
            f"{api_base}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": model,
                "temperature": 0.2,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a startup strategy analyst. Return strict JSON only.",
                    },
                    {"role": "user", "content": prompt},
                ],
            },
        )

    if response.status_code >= 400:
        raise LLMProviderError(f"Provider HTTP {response.status_code}: {response.text[:220]}")

    return _extract_openai_text(response.json())


def call_openrouter(prompt: str) -> str:
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    if not api_key:
        raise LLMProviderError("OPENROUTER_API_KEY missing")

    model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
    with httpx.Client(timeout=45.0) as client:
        response = client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": os.getenv("OPENROUTER_REFERER", "http://localhost:3000"),
                "X-Title": "StartupDocs",
            },
            json={
                "model": model,
                "temperature": 0.2,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a startup strategy analyst. Return strict JSON only.",
                    },
                    {"role": "user", "content": prompt},
                ],
            },
        )

    if response.status_code >= 400:
        raise LLMProviderError(
            f"OpenRouter HTTP {response.status_code}: {response.text[:220]}"
        )

    return _extract_openai_text(response.json())


def call_groq(prompt: str) -> str:
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        raise LLMProviderError("GROQ_API_KEY missing")

    model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    return _call_openai_compatible(
        api_base="https://api.groq.com/openai/v1",
        api_key=api_key,
        model=model,
        prompt=prompt,
    )


def call_mistral(prompt: str) -> str:
    api_key = os.getenv("MISTRAL_API_KEY", "")
    if not api_key:
        raise LLMProviderError("MISTRAL_API_KEY missing")

    model = os.getenv("MISTRAL_MODEL", "mistral-small-latest")
    return _call_openai_compatible(
        api_base="https://api.mistral.ai/v1",
        api_key=api_key,
        model=model,
        prompt=prompt,
    )


def call_gemini(prompt: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        raise LLMProviderError("GEMINI_API_KEY missing")

    model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={api_key}"
    )

    with httpx.Client(timeout=45.0) as client:
        response = client.post(
            url,
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.2},
            },
        )

    if response.status_code >= 400:
        raise LLMProviderError(f"Gemini HTTP {response.status_code}: {response.text[:220]}")

    data = response.json()
    candidates = data.get("candidates", [])
    if not candidates:
        raise LLMProviderError("Gemini returned no candidates")

    parts = candidates[0].get("content", {}).get("parts", [])
    if not parts:
        raise LLMProviderError("Gemini returned no content parts")

    text = parts[0].get("text")
    if not isinstance(text, str) or not text.strip():
        raise LLMProviderError("Gemini returned empty content")

    return text


def call_provider(provider_name: str, prompt: str) -> str:
    provider = provider_name.strip().lower()
    if provider == "openrouter":
        return call_openrouter(prompt)
    if provider == "groq":
        return call_groq(prompt)
    if provider == "gemini":
        return call_gemini(prompt)
    if provider == "mistral":
        return call_mistral(prompt)
    raise LLMProviderError(f"Unsupported provider: {provider_name}")
