# AiNews → Sofon (sofon.diusai.org/ainews)

Drop-in stránka, ktorá pridá AI News Monitor ako podstránku do Sofon Next.js appky.
Štýl využíva CSS premenné a fonty, ktoré Sofon už má (holo-cyan, coral, Orbitron, Rajdhani),
takže zapadne bez ďalšieho nastavovania.

## Čo skopírovať do Sofon repa (2 súbory)

1. **`page.tsx`**  →  `src/app/ainews/page.tsx`
   (vytvorí route `sofon.diusai.org/ainews`)

2. **dáta**  →  `public/ainews-data.json`
   Skopíruj sem `dashboard/data.json` z AiNews repa
   (to je výstup pipeline — `python3 src/pipeline.py`).

Po nasadení Sofonu bude AiNews na `sofon.diusai.org/ainews`.

## Odkiaľ sa berú dáta

Python pipeline v AiNews repe (`src/pipeline.py`) každé ráno:
zber RSS/API + GitHub repá → filter → dedup → Gemini triedenie → `dashboard/data.json`.

Pre automatický denný update v Sofone stačí, aby sa `data.json` raz denne
prekopíroval do `public/ainews-data.json` (cez GitHub Action alebo cron).
Tento krok vieme doriešiť, keď bude stránka nasadená.

## Pozn.
- `page.tsx` je client component ("use client"), číta `/ainews-data.json` cez fetch.
- Žiadne nové závislosti — používa len React (ktorý Sofon má).
