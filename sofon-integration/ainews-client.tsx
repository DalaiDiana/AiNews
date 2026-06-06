"use client";

// AI News Monitor — klientská (interaktívna) časť. Dáta dostáva ako prop
// zo server-komponentu page.tsx (preto je obsah v HTML a prečítajú ho aj roboty).

import { useEffect, useMemo, useState } from "react";

type Item = { title: string; url: string; summary: string; source: string; region: string; published: string; added?: string; category: string; };
type Cat = { items: Item[]; new: number };
type Data = { generated: string; today: string; total_new: number; total_items: number; categories: Record<string, Cat> };

const META: Record<string, [string, string, string]> = {
  bigplayers: ["ti-building-skyscraper", "Big Players", "Corporate news from major labs and vendors — OpenAI, Anthropic, Google, Meta, Microsoft, Nvidia, plus Chinese and other players."],
  models: ["ti-box-multiple", "Models & Releases", "New model launches and updates: LLMs, image, video, audio and multimodal — plus text-to-speech, speech-to-text and translators."],
  agents: ["ti-robot", "Agents & Frameworks", "Agentic systems and dev tooling — MCP, LangChain, agent frameworks and consumer bots like Hermes and OpenClaw."],
  robotics: ["ti-robot-face", "Robotics", "Humanoid and general robotics powered by AI — new robots, demos, research and deployments."],
  autonomous: ["ti-car", "Autonomous Transport", "Self-driving cars, drones and autonomous mobility — technology, pilots and regulation-adjacent news."],
  gadgets: ["ti-device-watch", "Gadgets", "AI-powered hardware — smart glasses, wearables and data-collection devices, plus new chips and sensors."],
  memory: ["ti-brain", "Memory", "Advances in AI memory — long-term and context memory, memory products and research on how models store and recall information."],
  github: ["ti-brand-github", "GitHub", "Trending and most-starred AI/ML repositories — new open-source projects, libraries and tools gaining traction."],
  infra: ["ti-server-2", "Infrastructure & Compute", "Data centers, GPUs and accelerators, cloud and the hardware and energy backbone behind AI."],
  benchmarks: ["ti-chart-bar", "Benchmarks & Evaluations", "New benchmarks, leaderboards and eval methods — how models are measured and compared."],
  research: ["ti-flask", "Science & Research", "Real-world applications of AI across science and industry, plus notable papers and use-cases."],
  business: ["ti-coin", "Business & Funding", "Investments, funding rounds, acquisitions and market moves — including funding calls and grants."],
  legislation: ["ti-gavel", "Legislation", "Laws, regulations and policy on AI worldwide — the EU AI Act, national rules and enforcement."],
  ethics: ["ti-scale", "Philosophy, Ethics & Safety", "Alignment, AI safety, ethics and the broader philosophical debate."],
  skcz: ["ti-map-pin", "Slovakia & Czechia", "The most important AI news from Slovakia and the Czech Republic."],
};
const ORDER = ["bigplayers","models","agents","robotics","autonomous","gadgets","memory","github","infra","benchmarks","research","business","legislation","ethics","skcz"];
const REGIONS: [string, string][] = [["ALL","ALL"],["US","US"],["EU","EU"],["CN","CN"],["IN","IN"],["SK / CZ","SKCZ"]];
const CY = "#00c3ff", CORAL = "#E8726A";
const regColor = (r: string) => r === "CN" ? CORAL : r === "EU" ? "#a08cff" : r === "IN" ? "#e0af68" : (r === "SK" || r === "CZ") ? "#73d3a8" : CY;
const EXT = "https://raw.githubusercontent.com/DalaiDiana/AiNews/main/dashboard/data.json";

function ago(iso: string) { const s = (Date.now() - new Date(iso).getTime()) / 1000;
  if (s < 3600) return Math.max(1, Math.round(s / 60)) + "m"; if (s < 86400) return Math.round(s / 3600) + "h"; return Math.round(s / 86400) + "d"; }
function cleanDesc(html: string) { if (!html) return "";
  const tmp = typeof document !== "undefined" ? document.createElement("div") : null; let t = html;
  if (tmp) { tmp.innerHTML = html; t = tmp.textContent || ""; }
  t = t.replace(/\s+/g, " ").trim(); const parts = t.match(/[^.!?]+[.!?]+/g);
  if (parts && parts.length) t = parts.slice(0, 3).join(" ").trim(); if (t.length > 300) t = t.slice(0, 297).trim() + "…"; return t; }

export default function AiNewsClient({ data: initial }: { data: Data | null }) {
  const [data, setData] = useState<Data | null>(initial);
  const [region, setRegion] = useState("ALL");
  const [open, setOpen] = useState<string | null>(null);

  useEffect(() => { if (!data) fetch(EXT, { cache: "no-store" }).then(r => r.json()).then(setData).catch(() => {}); }, [data]);

  const sourceCount = useMemo(() => {
    if (!data) return 0; const s = new Set<string>();
    Object.values(data.categories || {}).forEach(c => c.items.forEach(i => s.add(i.source))); return s.size;
  }, [data]);

  const visible = (cat: string): Item[] => {
    const items = data?.categories?.[cat]?.items || [];
    if (region === "ALL") return items;
    if (region === "SKCZ") return items.filter(i => i.region === "SK" || i.region === "CZ");
    return items.filter(i => i.region === region);
  };
  const openCat = (id: string) => { setOpen(id); if (typeof window !== "undefined") window.scrollTo({ top: 0, behavior: "smooth" }); };

  if (!data) return (<main style={{ minHeight: "60vh", display: "grid", placeItems: "center", color: "var(--foreground,#c8e6ff)", fontFamily: "var(--font-mono)" }}>loading AI News Monitor…</main>);

  const sync = new Date(data.generated).toISOString().slice(0, 16).replace("T", " ");

  return (
    <main className="ainm-wrap" style={{ color: "var(--foreground,#c8e6ff)", fontFamily: "var(--font-sans)" }}>
      <style>{`
        @import url('https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@3.7.0/dist/tabler-icons.min.css');
        .ainm-wrap{max-width:none;width:100%;margin:0;padding:40px clamp(18px,3vw,64px) 90px;}
        .ainm-grid{display:grid;gap:14px;grid-template-columns:repeat(4,1fr);}
        @media (max-width:800px){ .ainm-grid{grid-template-columns:repeat(2,1fr);} }
        @media (max-width:500px){ .ainm-wrap{padding:22px 14px 60px;} .ainm-grid{gap:10px;} .ainm-counter{font-size:30px !important;} }
        .ainm-tile{background:rgba(0,15,40,.55);border:1px solid rgba(0,195,255,.16);border-radius:12px;padding:18px 18px 16px;cursor:pointer;position:relative;transition:.15s;}
        .ainm-tile:hover{border-color:rgba(0,195,255,.5);background:rgba(0,25,55,.6);transform:translateY(-2px);}
        .ainm-back{display:inline-flex;align-items:center;gap:8px;font-family:var(--font-mono);font-size:14px;color:${CY};background:transparent;border:1px solid rgba(0,195,255,.3);border-radius:8px;padding:8px 14px;cursor:pointer;margin:8px 0 18px;}
        .ainm-back:hover{background:rgba(0,195,255,.1);}
        .ainm-a:hover{color:#bfeaff !important;}
      `}</style>

      <header style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between", flexWrap: "wrap", gap: 20, paddingBottom: 18, borderBottom: "1px solid rgba(0,195,255,.18)" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <span style={{ width: 9, height: 9, borderRadius: "50%", background: CORAL, boxShadow: `0 0 12px ${CORAL}` }} />
            <span style={{ fontFamily: "var(--font-mono)", fontSize: 28, fontWeight: 700, letterSpacing: 1, color: "#eaf7ff", textShadow: "0 0 16px rgba(0,195,255,.4)" }}>AI NEWS <span style={{ color: CY }}>MONITOR</span></span>
          </div>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: 13.5, color: "rgba(184,232,255,.55)", marginTop: 10, letterSpacing: .5 }}>
            last sync {sync} UTC · {data.total_items} archived · {sourceCount} sources · powered by Gemini
          </div>
        </div>
        <div style={{ textAlign: "right", lineHeight: 1.1 }}>
          <div className="ainm-counter" style={{ fontFamily: "var(--font-mono)", fontSize: 46, fontWeight: 700, color: CORAL, textShadow: `0 0 18px rgba(232,114,106,.5)` }}>{data.total_new}</div>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: 11.5, letterSpacing: 2.5, textTransform: "uppercase", color: "rgba(184,232,255,.5)" }}>new today</div>
        </div>
      </header>

      {!open && (
        <>
          <section style={{ margin: "24px 0 4px", maxWidth: 820 }}>
            <h1 style={{ fontFamily: "var(--font-mono)", fontSize: 27, fontWeight: 600, color: "#eaf7ff", margin: "0 0 10px" }}>Everything new in AI, on one screen</h1>
            <p style={{ fontSize: 17, color: "rgba(184,232,255,.68)", margin: 0, lineHeight: 1.55 }}>A daily radar that gathers headlines from across labs, research, GitHub, robotics, policy and more. Every morning it removes duplicates and sorts each item into a single topic, keeping the last ten days. Pick a topic to see what just dropped.</p>
          </section>

          <div style={{ display: "flex", gap: 7, flexWrap: "wrap", margin: "22px 0 4px" }}>
            {REGIONS.map(([lbl, val]) => { const on = region === val; return (
              <button key={val} onClick={() => setRegion(val)} style={{ fontFamily: "var(--font-mono)", fontSize: 14, letterSpacing: .6, padding: "8px 16px", borderRadius: 7, cursor: "pointer", color: on ? CY : "rgba(184,232,255,.6)", background: on ? "rgba(0,195,255,.1)" : "transparent", border: `1px solid ${on ? "rgba(0,195,255,.5)" : "rgba(0,195,255,.16)"}` }}>{lbl}</button>
            ); })}
          </div>

          <div className="ainm-grid" style={{ marginTop: 16 }}>
            {ORDER.map(id => { const meta = META[id]; if (!meta) return null;
              const c = data.categories[id] || { items: [], new: 0 }; const items = visible(id);
              return (
                <div key={id} className="ainm-tile" onClick={() => openCat(id)}>
                  <i className={"ti " + meta[0]} aria-hidden="true" style={{ fontSize: 36, color: CY, opacity: .9 }} />
                  <div style={{ fontSize: 20, fontWeight: 600, color: "#dff3ff", marginTop: 14 }}>{meta[1]}</div>
                  <div style={{ fontFamily: "var(--font-mono)", fontSize: 14, color: "rgba(184,232,255,.45)", marginTop: 6 }}>{items.length} items</div>
                  <div style={{ position: "absolute", top: 15, right: 15, fontFamily: "var(--font-mono)", fontSize: 13, fontWeight: 600, padding: "4px 10px", borderRadius: 7, color: c.new ? CORAL : "rgba(184,232,255,.4)", background: c.new ? "rgba(232,114,106,.13)" : "transparent", border: `1px solid ${c.new ? "rgba(232,114,106,.3)" : "rgba(0,195,255,.16)"}` }}>{c.new} new</div>
                </div>
              ); })}
          </div>
        </>
      )}

      {open && (() => {
        const meta = META[open]; const items = visible(open);
        return (
          <div style={{ marginTop: 22 }}>
            <button className="ainm-back" onClick={() => setOpen(null)}><i className="ti ti-arrow-left" aria-hidden="true" /> Back to topics</button>
            <h2 style={{ fontFamily: "var(--font-mono)", margin: 0, fontSize: 26, fontWeight: 600, color: "#eaf7ff", display: "flex", alignItems: "center", gap: 12 }}><i className={"ti " + meta[0]} aria-hidden="true" style={{ color: CY, fontSize: 32 }} />{meta[1]} <span style={{ color: "rgba(184,232,255,.4)", fontSize: 14, fontWeight: 400 }}>· {items.length} shown</span></h2>
            <p style={{ fontSize: 16, color: "rgba(184,232,255,.62)", margin: "11px 0 18px", maxWidth: 900, lineHeight: 1.5 }}>{meta[2]}</p>
            {items.length === 0 && <p style={{ color: "rgba(184,232,255,.4)", fontSize: 14 }}>No items for this filter.</p>}
            {items.slice(0, 80).map((it, k) => {
              const isNew = it.added === data.today; const desc = cleanDesc(it.summary);
              return (
                <div key={k} style={{ padding: isNew ? "16px 14px" : "16px 0", borderTop: "1px solid rgba(0,195,255,.1)", background: isNew ? "rgba(232,114,106,.09)" : "transparent", borderLeft: isNew ? `3px solid ${CORAL}` : "3px solid transparent", borderRadius: isNew ? 6 : 0 }}>
                  <div style={{ display: "flex", gap: 13, alignItems: "baseline" }}>
                    <span style={{ fontFamily: "var(--font-mono)", fontSize: 12.5, letterSpacing: .8, color: regColor(it.region), border: `1px solid ${regColor(it.region)}55`, padding: "3px 9px", borderRadius: 5, minWidth: 40, textAlign: "center", whiteSpace: "nowrap" }}>{it.region}</span>
                    <a className="ainm-a" href={it.url} target="_blank" rel="noopener noreferrer" style={{ color: "#eaf7ff", textDecoration: "none", fontSize: 19, fontWeight: 500, lineHeight: 1.45 }}>{isNew && <span style={{ display: "inline-block", width: 7, height: 7, borderRadius: "50%", background: CORAL, marginRight: 8 }} />}{it.title}</a>
                    <span style={{ fontFamily: "var(--font-mono)", fontSize: 13.5, color: "rgba(184,232,255,.45)", marginLeft: "auto", whiteSpace: "nowrap", paddingLeft: 12 }}>{it.source} · {ago(it.published)}</span>
                  </div>
                  {desc && <div style={{ fontSize: 16, color: "rgba(184,232,255,.64)", lineHeight: 1.55, margin: "8px 0 0 54px" }}>{desc}</div>}
                </div>
              );
            })}
          </div>
        );
      })()}
    </main>
  );
}
