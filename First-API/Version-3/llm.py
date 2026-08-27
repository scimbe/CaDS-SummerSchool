"""Minimaler Client für den OpenAI-kompatiblen Endpoint - nur Python-Standardbibliothek.

Damit die Beispielskripte ohne 'pip install' laufen. Wer möchte, nutzt
stattdessen das offizielle SDK (siehe 06_openai_sdk.py) - die Aufrufe sind identisch.
"""
import json
import os
import urllib.request
from pathlib import Path


def _load_env() -> None:
    """Sucht .env neben dieser Datei und in den Elternordnern, lädt sie in os.environ.

    (Bestehende Umgebungsvariablen gewinnen - so kann man Werte im Terminal überschreiben.)
    """
    here = Path(__file__).resolve().parent
    for ordner in [here, *here.parents]:
        env_file = ordner / ".env"
        if env_file.exists():
            break
    else:
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


_load_env()

BASE_URL = os.environ.get("LLM_BASE_URL", "").rstrip("/")
API_KEY = os.environ.get("LLM_API_KEY", "")
MODEL = os.environ.get("LLM_MODEL", "local-devstral-small2")

if not BASE_URL or not API_KEY:
    raise SystemExit("LLM_BASE_URL / LLM_API_KEY fehlen - bitte .env anlegen (siehe .env.example).")


def _request(path: str, payload: dict, stream: bool = False):
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    return urllib.request.urlopen(req, timeout=300)


def chat(messages, *, tools=None, temperature=0.7, max_tokens=800, **extra) -> dict:
    """Eine Anfrage, eine vollständige Antwort. Gibt die message des Modells zurück."""
    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        **extra,
    }
    if tools:
        payload["tools"] = tools
    with _request("/chat/completions", payload) as resp:
        data = json.loads(resp.read())
    return data["choices"][0]["message"]


def ask(prompt: str, system: str | None = None, **kwargs) -> str:
    """Bequemer Einzeiler: Frage rein, Text raus."""
    messages = ([{"role": "system", "content": system}] if system else []) + [
        {"role": "user", "content": prompt}
    ]
    return chat(messages, **kwargs).get("content", "")


def stream(messages, **kwargs):
    """Wie chat(), liefert die Antwort aber stückweise als Generator von Text-Schnipseln."""
    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": True,
        "temperature": kwargs.pop("temperature", 0.7),
        "max_tokens": kwargs.pop("max_tokens", 800),
        **kwargs,
    }
    with _request("/chat/completions", payload, stream=True) as resp:
        for raw in resp:
            line = raw.decode("utf-8").strip()
            if not line.startswith("data:"):
                continue
            data = line[5:].strip()
            if data == "[DONE]":
                return
            delta = json.loads(data)["choices"][0].get("delta", {})
            if delta.get("content"):
                yield delta["content"]
