"use client";

// AI News Monitor — Next.js stránka pre Sofon (sofon.diusai.org/ainews)
// Umiestnenie v Sofone: src/app/ainews/page.tsx
// Dáta: public/ainews-data.json  (generuje Python pipeline z AiNews repa)
// Štýl využíva CSS premenné zo Sofon globals.css (--holo-cyan, --coral, ...).

import { useEffect, useMemo, useState } from "react";

type Item = {
  title: string; url: string; summary: string;
  source: string; region: string; published: string; added?: string; category: string;
};
type Cat = { items: Item[]; new: number };
type Data = { generated: string; today: string; total_new: number; total_items: number; categories: Record<string, Cat> };

const META: Record<string, [string, string]> = {
  bigplayers: ["Big Players", "Corporate news from major labs and vendors — OpenAI, Anthropic, Google, Meta, Microsoft, Nvidia, plus Chinese and other players."],
  models: ["Models & Releases", "New model launches and updates: LLMs, image, video, audio and multimodal — plus text-to-speech, speech-to-text and translators."],
  agents: ["Agents & Frameworks", "Agentic systems and dev tooling — MCP, LangChain, agent frameworks and consumer bots like Hermes and OpenClaw."],
  robotics: ["Robotics", "Humanoid and general robotics powered by AI — new robots, demos, research and deployments."],
  autonomous: ["Autonomous Transport", "Self-driving cars, drones and autonomous mobility — technology, pilots and regulation-adjacent news."],
  gadgets: ["Gadgets", "AI-powered hardware — smart glasses, wearables and data-collection devices, plus new chips and sensors."],
  memory: ["Memory", "Advances in AI memory — long-term and context memory, memory products and research on how models store and recall information."],
  github: ["GitHub", "Trending and most-starred AI/ML repositories — new open-source projects, libraries and tools gaining traction."],
  infra: ["Infrastructure & Compute", "Data centers, GPUs and accelerators, cloud and the hardware and energy backbone behind AI."],
  benchmarks: ["Benchmarks & Evaluations", "New benchmarks, leaderboards and eval methods — how models are measured and compared."],
  research: ["Science & Research", "Real-world applications of AI across science and industry, plus notable papers and use-cases."],
  business: ["Business & Funding", "Investments, funding rounds, acquisitions and market moves — including funding calls and grants."],
  legislation: ["Legislation", "Laws, regulations and policy on AI worldwide — the EU AI Act, national rules and enforcement."],
  ethics: ["Philosophy, Ethics & Safety", "Alignment, AI safety, ethics and the broader philosophical debate."],
  skcz: ["Slovakia & Czechia", "The most important AI news from Slovakia and the Czech Republic."],
};
const ORDER = ["bigplayers","models","agents","robotics","autonomous","gadgets","memory","github","infra","benchmarks","research","business","legislation","ethics","skcz"];
const REGIONS: [string, string][] = [["ALL","ALL"],["US","US"],["EU","EU"],["CN","CN"],["IN","IN"],["SK / CZ","SKCZ"]];

const CY = "#00c3ff", CORAL = "#E8726A";
const regColor = (r: string) => r === "CN" ? CORAL : r === "EU" ? "#a08cff" : r === "IN" ? "#e0af68" : (r === "SK" || r === "CZ") ? "#73d3a8" : CY;

function ago(iso: string) {
  const s = (Date.now() - new Date(iso).getTime()) / 1000;
  if (s < 3600) return Math.max(1, Math.round(s / 60)) + "m";
  if (s < 86400) return Math.round(s / 3600) + "h";
  return Math.round(s / 86400) + "d";
}
function cleanDesc(html: string) {
  if (!html) return "";
  const tmp = typeof document !== "undefined" ? document.createElement("div") : null;
  let t = html;
  if (tmp) { tmp.innerHTML = html; t = tmp.textContent || ""; }
  t = t.replace(/\s+/g, " ").trim();
  const parts = t.match(/[^.!?]+[.!?]+/g);
  if (parts && parts.length) t = parts.slice(0, 3).join(" ").trim();
  if (t.length > 300) t = t.slice(0, 297).trim() + "…";
  return t;
}

export default function AiNewsPage() {
  const [data, setData] = useState<Data | null>(null);
  const [region, setRegion] = useState("ALL");
  const [open, setOpen] = useState<string | null>(null);

  useEffect(() => {
    fetch("/ainews-data.json").then(r => r.json()).then(setData).catch(() => {});
  }, []);

  const visible = useMemo(() => (cat: string): Item[] => {
    const items = data?.categories?.[cat]?.items || [];
    if (region === "ALL") return items;
    if (region === "SKCZ") return items.filter(i => i.region === "SK" || i.region === "CZ");
    return items.filter(i => i.region === region);
  }, [data, region]);

  if (!data) return (
    <main style={{ minHeight: "60vh", display: "grid", placeItems: "center", color: "var(--foreground,#c8e6ff)", fontFamily: "var(--font-mono)" }}>
      loading AI News Monitor…
    </main>
  );

  const sync = new Date(data.generated).toISOString().slice(0, 16).replace("T", " ");

  return (
    <main style={{ maxWidth: 1120, margin: "0 auto", padding: "40px 26px 80px", color: "var(--foreground,#c8e6ff)", fontFamily: "var(--font-sans)" }}>
      <header style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between", flexWrap: "wrap", gap: 20, paddingBottom: 18, borderBottom: "1px solid rgba(0,195,255,.18)" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <span style={{ width: 9, height: 9, borderRadius: "50%", background: CORAL, boxShadow: `0 0 12px ${CORAL}` }} />
            <span style={{ fontFamily: "var(--font-mono)", fontSize: 22, fontWeight: 700, letterSpacing: 1, color: "#eaf7ff", textShadow: "0 0 16px rgba(0,195,255,.4)" }}>
              AI NEWS <span style={{ color: CY }}>MONITOR</span>
            </span>
          </div>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "rgba(184,232,255,.5)", marginTop: 9, letterSpacing: .5 }}>
            last sync {sync} UTC · {data.total_items} archived · powered by Gemini
          </div>
        </div>
        <div style={{ textAlign: "right", lineHeight: 1.1 }}>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: 36, fontWeight: 700, color: CORAL, textShadow: `0 0 18px rgba(232,114,106,.5)` }}>{data.total_new}</div>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: 10, letterSpacing: 2.5, textTransform: "uppercase", color: "rgba(184,232,255,.5)" }}>new today</div>
        </div>
      </header>

      <section style={{ margin: "24px 0 4px", maxWidth: 760 }}>
        <h1 style={{ fontFamily: "var(--font-mono)", fontSize: 20, fontWeight: 600, color: "#eaf7ff", margin: "0 0 8px" }}>Everything new in AI, on one screen</h1>
        <p style={{ fontSize: 15, color: "rgba(184,232,255,.65)", margin: 0 }}>
          A daily radar that gathers headlines from across labs, research, GitHub, robotics, policy and more. Every morning it removes duplicates and sorts each item into a single topic, keeping the last ten days. Pick a topic to see what just dropped.
        </p>
      </section>

      <div style={{ display: "flex", gap: 7, flexWrap: "wrap", margin: "22px 0 4px" }}>
        {REGIONS.map(([lbl, val]) => {
          const on = region === val;
          return (
            <button key={val} onClick={() => { setRegion(val); setOpen(null); }}
              style={{ fontFamily: "var(--font-mono)", fontSize: 11, letterSpacing: .6, padding: "6px 13px", borderRadius: 7, cursor: "pointer",
                color: on ? CY : "rgba(184,232,255,.6)", background: on ? "rgba(0,195,255,.1)" : "transparent",
                border: `1px solid ${on ? "rgba(0,195,255,.5)" : "rgba(0,195,255,.16)"}` }}>{lbl}</button>
          );
        })}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))", gap: 13, marginTop: 16 }}>
        {ORDER.map(id => {
          const meta = META[id]; if (!meta) return null;
          const c = data.categories[id] || { items: [], new: 0 };
          const items = visible(id);
          return (
            <div key={id} onClick={() => setOpen(id)}
              style={{ background: "rgba(0,15,40,.55)", border: "1px solid rgba(0,195,255,.16)", borderRadius: 12, padding: "17px 17px 15px", cursor: "pointer", position: "relative" }}>
              <div style={{ fontSize: 13.5, fontWeight: 600, color: "#dff3ff" }}>{meta[0]}</div>
              <div style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "rgba(184,232,255,.45)", marginTop: 4 }}>{items.length} items</div>
              <div style={{ position: "absolute", top: 15, right: 15, fontFamily: "var(--font-mono)", fontSize: 11, fontWeight: 600, padding: "3px 9px", borderRadius: 7,
                color: c.new ? CORAL : "rgba(184,232,255,.4)", background: c.new ? "rgba(232,114,106,.13)" : "transparent",
                border: `1px solid ${c.new ? "rgba(232,114,106,.3)" : "rgba(0,195,255,.16)"}` }}>{c.new} new</div>
            </div>
          );
        })}
      </div>

      {open && (() => {
        const meta = META[open]; const items = visible(open);
        return (
          <div style={{ marginTop: 24, border: "1px solid rgba(0,195,255,.2)", borderRadius: 12, background: "rgba(0,15,40,.5)", padding: "22px 24px" }}>
            <h2 style={{ fontFamily: "var(--font-mono)", margin: 0, fontSize: 16, fontWeight: 600, color: "#eaf7ff" }}>{meta[0]} <span style={{ color: "rgba(184,232,255,.4)", fontSize: 11, fontWeight: 400 }}>· {items.length} shown</span></h2>
            <p style={{ fontSize: 12.5, color: "rgba(184,232,255,.6)", margin: "9px 0 14px", maxWidth: 800 }}>{meta[1]}</p>
            {items.slice(0, 60).map((it, k) => {
              const isNew = it.added === data.today; const desc = cleanDesc(it.summary);
              return (
                <div key={k} style={{ padding: "14px 0", borderTop: "1px solid rgba(0,195,255,.1)" }}>
                  <div style={{ display: "flex", gap: 13, alignItems: "baseline" }}>
                    <span style={{ fontFamily: "var(--font-mono)", fontSize: 9.5, letterSpacing: .8, color: regColor(it.region), border: `1px solid ${regColor(it.region)}55`, padding: "2px 7px", borderRadius: 5, minWidth: 34, textAlign: "center", whiteSpace: "nowrap" }}>{it.region}</span>
                    <a href={it.url} target="_blank" rel="noopener noreferrer" style={{ color: "#eaf7ff", textDecoration: "none", fontSize: 14, fontWeight: 500, lineHeight: 1.45 }}>
                      {isNew && <span style={{ display: "inline-block", width: 5, height: 5, borderRadius: "50%", background: CORAL, marginRight: 7 }} />}{it.title}
                    </a>
                    <span style={{ fontFamily: "var(--font-mono)", fontSize: 10.5, color: "rgba(184,232,255,.4)", marginLeft: "auto", whiteSpace: "nowrap", paddingLeft: 12 }}>{it.source} · {ago(it.published)}</span>
                  </div>
                  {desc && <div style={{ fontSize: 12, color: "rgba(184,232,255,.6)", lineHeight: 1.55, margin: "6px 0 0 47px" }}>{desc}</div>}
                </div>
              );
            })}
          </div>
        );
      })()}
    </main>
  );
}
