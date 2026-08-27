# Warum OpenAI-kompatibel wichtig ist

Der Endpunkt spricht dasselbe Protokoll wie die OpenAI-API. In `07_openai_sdk.py`
sieht man, was das praktisch bedeutet:

```python
client = OpenAI(
    base_url="https://llm-…/v1",   # der einzige Unterschied
    api_key="sk-…",
)
```

Zwei Zeilen. Danach funktioniert das offizielle SDK — mit einem Modell, das auf
eigener Hardware läuft.

## Warum das mehr ist als Bequemlichkeit

**Das Ökosystem kommt gratis mit.** Alles, was gegen OpenAI gebaut wurde,
funktioniert: SDKs für jede Sprache, LangChain, LlamaIndex, Coding-Agenten,
Chat-Oberflächen, Monitoring-Werkzeuge. Nichts davon musste für dieses Modell
angepasst werden.

**Der Anbieter wird austauschbar.** Wer heute lokal entwickelt und morgen ein
größeres Modell braucht, ändert eine Umgebungsvariable. Und umgekehrt: Wer
feststellt, dass Daten das Haus nicht verlassen dürfen, zieht denselben Code auf
den eigenen Endpunkt um. Ohne Umbau bleibt das eine Entscheidung, keine Migration.

**Vergleichen wird möglich.** Dieselbe Anwendung mit drei Modellen laufen zu
lassen kostet drei `.env`-Dateien. Genau das ist der Weg, um herauszufinden, ob
ein großes Modell für die eigene Aufgabe überhaupt einen Unterschied macht —
und das ist erstaunlich oft nicht der Fall, wenn das Harness stimmt.

## Was Kompatibilität nicht garantiert

Kompatibel heißt: dieselben Pfade, dieselben Felder. Es heißt nicht: derselbe
Funktionsumfang.

<p class="gemessen" markdown>
**An dieser Installation gemessen:** <code>/v1/chat/completions</code>
funktioniert mit und ohne Streaming, Tool-Calling funktioniert auch mit mehreren
Aufrufen in einer Antwort. <code>/v1/embeddings</code> antwortet mit HTTP 400 —
für semantische Suche braucht es einen anderen Dienst.
</p>

Ebenfalls nicht garantiert: Wie gut das Modell die Vorgaben befolgt. Ein
`enum` im Tool-Schema ist eine Beschreibung, keine Einschränkung — das Modell
kann etwas anderes hineinschreiben. Deshalb prüft `pruefe_plan()` in Version-3
jeden Wert erneut, obwohl das Schema ihn schon vorgibt.

## Die praktische Folge für diesen Kurs

`llm.py` hat rund 90 Zeilen und benutzt nur `urllib`. Das ist kein Purismus,
sondern Anschauung: Wer einmal gesehen hat, dass hinter „LLM-API" ein HTTP-POST
mit JSON steckt, liest danach jede SDK-Dokumentation anders — und weiß im
Fehlerfall, wo er nachsehen muss.
