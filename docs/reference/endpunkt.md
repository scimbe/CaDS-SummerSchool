# Der Endpunkt

OpenAI-kompatibel. Alles, was für OpenAI geschrieben wurde, funktioniert mit
geänderter `base_url` und `api_key`.

## Zugang

```bash
LLM_BASE_URL=https://llm-34a13a96.bunsenbrenner.org/v1
LLM_API_KEY=sk-…
LLM_MODEL=local-devstral-small2
```

## Verfügbare Pfade

| Pfad | Methode | Status |
|---|---|---|
| `/v1/models` | GET | ✅ liefert die Modellliste |
| `/v1/chat/completions` | POST | ✅ mit und ohne `stream` |
| `/v1/embeddings` | POST | ❌ antwortet mit HTTP 400 |

<p class="gemessen" markdown>
**An dieser Installation gemessen:** Die Modellliste enthält genau ein Modell,
<code>local-devstral-small2</code>. Tool-Calling funktioniert, auch mit mehreren
Aufrufen in einer Antwort. Embeddings sind nicht verfügbar — für semantische
Suche oder RAG braucht es einen anderen Dienst.
</p>

## Anfrage

```json
{
  "model": "local-devstral-small2",
  "messages": [
    {"role": "system", "content": "…"},
    {"role": "user", "content": "…"}
  ],
  "temperature": 0.3,
  "max_tokens": 500,
  "stream": false,
  "tools": [ … ]
}
```

| Feld | Anmerkung |
|---|---|
| `messages` | Rollen `system`, `user`, `assistant`, `tool` |
| `temperature` | 0 bis ~1. Für Berichte 0.2–0.3 |
| `max_tokens` | Obergrenze der Antwort, nicht der Anfrage |
| `stream` | `true` liefert Server-Sent Events |
| `tools` | Liste von Funktionsbeschreibungen im JSON-Schema-Format |

## Antwort

```json
{
  "id": "chatcmpl-…",
  "model": "local-devstral-small2",
  "choices": [{
    "finish_reason": "stop",
    "message": {"role": "assistant", "content": "…"}
  }],
  "usage": {"prompt_tokens": 567, "completion_tokens": 33, "total_tokens": 600}
}
```

`finish_reason` ist `stop` bei normalem Ende, `tool_calls` bei einem
Funktionsaufruf, `length` wenn `max_tokens` erreicht wurde.

## Tool-Calling

```json
"message": {
  "role": "assistant",
  "content": "",
  "tool_calls": [{
    "id": "call_3z7ld1t5",
    "type": "function",
    "function": {"name": "get_weather", "arguments": "{\"city\": \"Hamburg\"}"}
  }]
}
```

`arguments` ist eine **Zeichenkette** mit JSON, kein Objekt — sie muss geparst
werden.

## Streaming

```
data: {"choices":[{"delta":{"content":"1"}}]}
data: {"choices":[{"delta":{"content":","}}]}
data: [DONE]
```

Jede Zeile beginnt mit `data: `, das Ende ist wörtlich `data: [DONE]`. Ein
Delta ohne `content` (etwa nur mit `role`) wird übersprungen.

## Fehlercodes

| Code | Ursache |
|---|---|
| 400 | Anfrage ungültig, oder der Pfad wird nicht unterstützt |
| 401 | Schlüssel falsch oder abgelaufen |
| 404 | Pfad falsch — meist fehlt `/v1` |
| 5xx | Endpunkt überlastet oder Modell nicht geladen |
