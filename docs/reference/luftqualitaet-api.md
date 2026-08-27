# Die Luftqualitäts-API

Quelle: [infranode.dev](https://infranode.dev/daten/luftqualitaet-api/).
Keylos, kostenlos, 300 Anfragen pro Minute und IP. Daten aus dem Messnetz des
Umweltbundesamts.

## Messwerte einer Stadt

```
GET https://infranode.dev/api/v1/cities/<slug>/air-uba
```

```bash
curl -s https://infranode.dev/api/v1/cities/hamburg/air-uba | jq .
```

```json
{
  "data": {
    "city_slug": "hamburg",
    "geo": {"lat": 53.5641, "lon": 9.9679},
    "observed_at": "2026-08-27T10:00:00Z",
    "retrieved_at": "2026-08-27T11:32:41Z",
    "source": "uba",
    "license_id": "dl_de_by_2_0",
    "attribution": {
      "text": "Umweltbundesamt (UBA)",
      "license_url": "https://www.govdata.de/dl-de/by-2-0",
      "modified": false
    },
    "payload": {
      "kind": "air_quality", "station_id": "784",
      "pm10": 23.0, "no2": 16.0, "pm25": 9.0, "o3": 79.0, "so2": 3.0
    }
  },
  "meta": {"source_status": "ok", "cache_status": "HIT"}
}
```

| Feld | Bedeutung |
|---|---|
| `payload.station_id` | Die nächstgelegene UBA-Station |
| `payload.pm10` … `so2` | Messwerte in µg/m³ |
| `observed_at` | Zeitpunkt der Messung (UTC) |
| `retrieved_at` | Zeitpunkt des Abrufs |
| `attribution` | Gehört in jede Weiterverwendung |

!!! warning "Nicht jede Station misst alles"
    Es kommen regelmäßig nur drei oder vier der fünf Werte. Und es kommt vor,
    dass eine Station antwortet, aber **gar keinen** Wert liefert. Beide Fälle
    sind normal und müssen behandelt werden — nicht als Ausnahme, sondern als
    Ergebnis.

## Städteliste {#staedteliste}

```
GET https://infranode.dev/api/v1/cities?limit=200
```

```json
{"data": [
  {"slug": "berlin", "name_de": "Berlin", "state": "BE",
   "population": 3782202, "geo": {…}, "coverage": "full"}
]}
```

84 Städte. In Version-3 ist diese Liste die **Whitelist**: Was nicht in ihr
steht, kann das Modell nicht anfragen.

```bash
curl -s "https://infranode.dev/api/v1/cities?limit=200" | jq -r '.data[].slug'
```

Slugs sind kleingeschrieben und ohne Umlaute: `muenchen`, `koeln`,
`duesseldorf`, `frankfurt-am-main`, `nuernberg`, `saarbruecken`.

## Lizenz

Die UBA-Daten stehen unter
[DL-DE BY 2.0](https://www.govdata.de/dl-de/by-2-0). Lizenz-URL und
Attributionstext stehen in jeder Antwort im `attribution`-Block und werden in
jedem erzeugten Bericht und in der Oberfläche mitgeführt.
