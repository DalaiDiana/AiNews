// AI News Monitor — SERVER komponent (sofon.diusai.org/ainews)
// Načíta dáta na serveri a vykreslí HTML => prečítajú to roboti/LLM/Google.
// Kategórie majú vlastnú adresu: /ainews?topic=robotics — server ju vyrenderuje aj s článkami,
// takže robot sa "preklikne" cez odkazy a prečíta obsah každej kategórie.
// Súbory v Sofone: src/app/ainews/page.tsx + ainews-client.tsx + opengraph-image.png

import AiNewsClient from "./ainews-client";

export const revalidate = 300;

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

export default async function Page({
  searchParams,
}: {
  searchParams: Promise<{ topic?: string }>;
}) {
  const sp = await searchParams;
  const data = await getData();
  return <AiNewsClient data={data} initialOpen={sp?.topic ?? null} />;
}
