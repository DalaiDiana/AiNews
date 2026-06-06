# AI News Monitor

Denný radar noviniek zo sveta AI. Ráno automaticky pozbiera správy z relevantných
zdrojov, zaradí ich do 15 kategórií a zobrazí na jednom dashboarde. Lokálne najprv.

## Ako to funguje (pipeline)

1. **fetch** — stiahne RSS/API zdroje (`config/sources.yaml`)
2. **filter** — nechá len posledných 24h + to, čo je o AI
3. **dedup** — ten istý článok z viacerých zdrojov → nechá originál
4. **classify** — zaradí každý článok do JEDNEJ kategórie (`config/categories.yaml`)
5. **store** — archív, expirovanie po 10 dňoch, počíta „N new"
6. **dashboard** — `dashboard/index.html` číta `dashboard/data.json`

## Spustenie

```bash
pip3 install -r requirements.txt
python3 src/pipeline.py         # vygeneruje dashboard/data.json + data.js
# otvor dashboard/index.html v prehliadači (dvojklik)
```

## Triedič (krok 4)

Ak je v koreni `credentials.json` (Google service account), zapne sa
**Gemini** (Vertex AI, model `gemini-2.5-flash-lite`, región `global`) a triedi
dávkovo podľa definícií kategórií. Bez neho beží záložný **keyword** režim.

GitHub repá majú vlastný zdroj (GitHub Search API) a vždy idú do kategórie
`github` — triedič ich nerieši, takže do GitHubu už nepadajú omylom články.

Kľúče NIKDY necommituj — `credentials.json`, `.env`, `*.key` sú v `.gitignore`.

## Stav

- Pipeline: fetch → filter → dedup → **Gemini** triedenie → archív (10 dní) → dashboard
- Zdroje: 17 overených RSS/API + GitHub trending repozitáre
- Dashboard: DiusAi farby + plexus pozadie

Ďalej: doplniť scraping zdroje (xAI, DeepSeek, čínske firmy), nastaviť denný
beh o 4:00 (GitHub Actions), prípadne nasadiť na doménu.
