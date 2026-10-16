// Server-side client for the Python agents service.
const BASE = process.env.AGENTS_BASE_URL ?? "http://localhost:8000";

export type AgentInfo = {
  id: "aeo" | "seo" | "competitor";
  name: string;
  description: string;
  input_schema: Record<string, unknown>;
};

export type AgentResult = {
  agent: string;
  summary: string;
  score: number | null;
  findings: Record<string, unknown>[];
  recommendations: string[];
  raw: Record<string, unknown>;
};

export async function listAgents(): Promise<AgentInfo[]> {
  const res = await fetch(`${BASE}/agents`, { cache: "no-store" });
  if (!res.ok) throw new Error(`agents service /agents -> ${res.status}`);
  return res.json();
}

export async function runAgent(
  agent: string,
  input: Record<string, unknown>
): Promise<AgentResult> {
  const res = await fetch(`${BASE}/run`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ agent, input }),
    cache: "no-store",
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`agents service /run -> ${res.status}: ${detail}`);
  }
  return res.json();
}
