"use client";

import { useEffect, useState } from "react";
import ResultView from "./ResultView";

type SchemaProp = {
  type?: string;
  description?: string;
  items?: { type?: string };
  default?: unknown;
};
type AgentInfo = {
  id: string;
  name: string;
  description: string;
  input_schema: {
    properties?: Record<string, SchemaProp>;
    required?: string[];
  };
};
type RunResult = {
  agent: string;
  summary: string;
  score: number | null;
  findings: Record<string, unknown>[];
  recommendations: string[];
  raw: Record<string, unknown>;
};

export default function Dashboard() {
  const [agents, setAgents] = useState<AgentInfo[]>([]);
  const [selected, setSelected] = useState<AgentInfo | null>(null);
  const [form, setForm] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<RunResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [provider, setProvider] = useState<{ provider: string; model: string | null } | null>(null);

  useEffect(() => {
    fetch("/api/agents")
      .then((r) => r.json())
      .then((d) => {
        if (Array.isArray(d)) setAgents(d);
        else setError(d.error ?? "Could not load agents");
      })
      .catch((e) => setError(String(e)));
    fetch("/api/providers")
      .then((r) => r.json())
      .then((d) => d?.provider && setProvider(d))
      .catch(() => {});
  }, []);

  function pick(a: AgentInfo) {
    setSelected(a);
    setResult(null);
    setError(null);
    const init: Record<string, string> = {};
    Object.entries(a.input_schema.properties ?? {}).forEach(([k, p]) => {
      init[k] = p.default != null ? String(p.default) : "";
    });
    setForm(init);
  }

  async function run() {
    if (!selected) return;
    setLoading(true);
    setError(null);
    setResult(null);
    const input = coerce(selected, form);
    try {
      const res = await fetch("/api/run", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ agent: selected.id, input }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error ?? "run failed");
      setResult(data.result);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
    {provider && (
      <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-white/10 bg-panel px-3 py-1 text-xs text-slate-300">
        <span className={`h-2 w-2 rounded-full ${provider.provider === "heuristic" ? "bg-amber-400" : "bg-emerald-400"}`} />
        Analysis engine: <span className="font-medium text-white">{provider.provider}</span>
        {provider.model && <span className="text-slate-500">· {provider.model}</span>}
        {provider.provider === "heuristic" && (
          <span className="text-slate-500">(no key — add one or run Ollama for richer output)</span>
        )}
      </div>
    )}
    <div className="grid md:grid-cols-3 gap-6">
      {/* agent catalog */}
      <div className="space-y-3">
        {error && !agents.length && (
          <div className="rounded-lg border border-red-500/40 bg-red-500/10 p-4 text-sm">
            {error}
          </div>
        )}
        {agents.map((a) => (
          <button
            key={a.id}
            onClick={() => pick(a)}
            className={`w-full text-left rounded-xl border p-4 transition ${
              selected?.id === a.id
                ? "border-accent bg-accent/10"
                : "border-white/10 bg-panel hover:border-white/25"
            }`}
          >
            <div className="font-medium">{a.name}</div>
            <div className="text-sm text-slate-400 mt-1">{a.description}</div>
          </button>
        ))}
      </div>

      {/* form + result */}
      <div className="md:col-span-2 space-y-6">
        {!selected && (
          <div className="rounded-xl border border-white/10 bg-panel p-8 text-center text-slate-400">
            Select an agent to run.
          </div>
        )}

        {selected && (
          <div className="rounded-xl border border-white/10 bg-panel p-6">
            <h2 className="font-medium mb-4">{selected.name}</h2>
            <div className="space-y-4">
              {Object.entries(selected.input_schema.properties ?? {}).map(([key, prop]) => {
                const required = selected.input_schema.required?.includes(key);
                const isArray = prop.type === "array";
                return (
                  <label key={key} className="block">
                    <span className="text-sm font-medium">
                      {key}
                      {required && <span className="text-accent"> *</span>}
                    </span>
                    {prop.description && (
                      <span className="block text-xs text-slate-500 mb-1">{prop.description}</span>
                    )}
                    {isArray ? (
                      <textarea
                        rows={3}
                        placeholder="one per line"
                        value={form[key] ?? ""}
                        onChange={(e) => setForm({ ...form, [key]: e.target.value })}
                        className="w-full rounded-md bg-ink border border-white/15 px-3 py-2 text-sm"
                      />
                    ) : (
                      <input
                        type={prop.type === "integer" ? "number" : "text"}
                        value={form[key] ?? ""}
                        onChange={(e) => setForm({ ...form, [key]: e.target.value })}
                        className="w-full rounded-md bg-ink border border-white/15 px-3 py-2 text-sm"
                      />
                    )}
                  </label>
                );
              })}
            </div>
            <button
              onClick={run}
              disabled={loading}
              className="mt-5 rounded-md bg-accent px-4 py-2 text-sm font-medium disabled:opacity-50"
            >
              {loading ? "Running…" : "Run agent"}
            </button>
            {error && selected && (
              <div className="mt-4 text-sm text-red-400">{error}</div>
            )}
          </div>
        )}

        {result && <ResultView result={result} />}
      </div>
    </div>
    </>
  );
}

// Turn the string form into the typed JSON the agent expects.
function coerce(agent: AgentInfo, form: Record<string, string>) {
  const out: Record<string, unknown> = {};
  Object.entries(agent.input_schema.properties ?? {}).forEach(([key, prop]) => {
    const v = (form[key] ?? "").trim();
    if (v === "") return;
    if (prop.type === "array") {
      out[key] = v.split("\n").map((s) => s.trim()).filter(Boolean);
    } else if (prop.type === "integer") {
      out[key] = Number(v);
    } else {
      out[key] = v;
    }
  });
  return out;
}
