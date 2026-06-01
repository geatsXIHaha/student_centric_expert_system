import json
import os
from pathlib import Path

import requests


def load_env_from_file(env_path=".env", override=False):

    path = Path(env_path)

    if not path.exists():
        return

    for line in path.read_text(encoding="utf-8").splitlines():

        text = line.strip()

        if not text or text.startswith("#") or "=" not in text:
            continue

        key, value = text.split("=", 1)

        key = key.strip()
        value = value.strip().strip("\"")

        if not key:
            continue

        if override or key not in os.environ:
            os.environ[key] = value


def build_prompt(profile, laptop, reasons):

    context = {

        "user_profile": profile,

        "system_reasons": reasons,

        "laptop": {
            "brand": laptop.get("Brand"),
            "model": laptop.get("Model"),
            "cpu": laptop.get("CPU"),
            "ram": laptop.get("RAM"),
            "storage": laptop.get("Storage"),
            "gpu": laptop.get("GPU"),
            "display": laptop.get("Display"),
            "price": laptop.get("Price"),
            "score": laptop.get("Score"),
        },
    }

    return (
        "You are an expert laptop advisor. "
        "Explain in one concise paragraph why the system recommended the laptop, "
        "based only on the provided user preferences and laptop specs. "
        "Do not mention internal scores or rules by name. "
        "Be clear, practical, and specific. "
        "Avoid marketing language.\n\n"
        f"Context (JSON):\n{json.dumps(context, ensure_ascii=True)}"
    )


def generate_llm_explanation(profile, laptop, reasons):

    load_env_from_file(override=True)

    api_key = os.getenv("GROQ_API_KEY")
    base_url = os.getenv(
        "GROQ_BASE_URL",
        "https://api.groq.com/openai/v1"
    )
    model = os.getenv(
        "GROQ_MODEL",
        "llama-3.1-8b-instant"
    )

    if not api_key:
        return (
            "Missing GROQ_API_KEY. "
            "Add it to your .env file."
        )

    prompt = build_prompt(
        profile,
        laptop,
        reasons
    )

    payload = {

        "model": model,

        "messages": [

            {
                "role": "system",
                "content": (
                    "You write concise and factual laptop recommendations."
                )
            },

            {
                "role": "user",
                "content": prompt
            }
        ],

        "temperature": 0.3,

        "max_tokens": 220
    }

    endpoint = f"{base_url.rstrip('/')}/chat/completions"

    print("\n========== GROQ DEBUG ==========")
    print("Endpoint:", endpoint)
    print("Model:", model)
    print("API Key:", api_key[:10] + "...")
    print("================================\n")

    try:

        response = requests.post(
            endpoint,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=20,
        )

        print("Status Code:", response.status_code)

        if response.status_code != 200:

            print("Response Body:")
            print(response.text)

            return (
                f"Groq API error: "
                f"{response.status_code}\n\n"
                f"{response.text}"
            )

        data = response.json()

        return (
            data["choices"][0]
            ["message"]
            ["content"]
            .strip()
        )

    except requests.exceptions.RequestException as exc:

        print("REQUEST EXCEPTION:")
        print(exc)

        return f"Groq API request failed: {exc}"

    except Exception as exc:

        print("UNEXPECTED ERROR:")
        print(exc)

        return f"Unexpected error: {exc}"