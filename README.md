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
pip install -r requirements.txt
python src/pipeline.py          # vygeneruje dashboard/data.json
# otvor dashboard/index.html v prehliadači
```

## Triedič (krok 4)

Bez kľúča beží **keyword** režim (lacný fallback). S Gemini kľúčom sa zapne
presnejší **Gemini Flash-Lite** režim (dávkové triedenie podľa definícií):

```bash
export GEMINI_API_KEY=...        # alebo GOOGLE_APPLICATION_CREDENTIALS=credentials.json
python src/pipeline.py
```

Kľúč NIKDY necommituj — `credentials.json`, `.env` a `*.key` sú v `.gitignore`.

## Stav

MVP: 18 overených RSS/API zdrojov. Ďalej: doplniť scraping zdroje (čínske firmy,
xAI, DeepSeek…), zapnúť Gemini triedič, nastaviť denný beh o 4:00 (cron / GitHub Actions),
doladiť sci-fi vizuál.
