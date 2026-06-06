// AI News Monitor — SERVER komponent (sofon.diusai.org/ainews)
// Načíta dáta na serveri a vykreslí ich do HTML => stránku prečítajú aj roboty/LLM/Google.
// Interaktivitu (filtre, rozbalenie, späť) rieši klientská časť ainews-client.tsx.
// Umiestnenie v Sofone: src/app/ainews/page.tsx (+ ainews-client.tsx, + opengraph-image.png)

import AiNewsClient from "./ainews-client";

export const revalidate = 300; // server si dáta obnoví max. raz za 5 min (bez redeployu)

export const metadata = {
  title: "AI News Monitor — everything new in AI",
  description:
    "A daily radar across labs, research, GitHub, robotics, policy and more — sorted into topics, refreshed every morning.",
};

const DATA_URL =
  "https://raw.githubusercontent.com/DalaiDiana/AiNews/main/dashboard/data.json";

async function getData() {
  try {
    const r = await fetch(DATA_URL, { next: { revalidate: 300 } });
    if (!r.ok) return null;
    return await r.json();
  } catch {
    return null;
  }
}

export default async function Page() {
  const data = await getData();
  return <AiNewsClient data={data} />;
}
