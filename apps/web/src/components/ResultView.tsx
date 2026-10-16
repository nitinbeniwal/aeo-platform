type RunResult = {
  agent: string;
  summary: string;
  score: number | null;
  findings: Record<string, unknown>[];
  recommendations: string[];
  raw: Record<string, unknown>;
};

export default function ResultView({ result }: { result: RunResult }) {
  return (
    <div className="rounded-xl border border-white/10 bg-panel p-6 space-y-5">
      <div className="flex items-start justify-between gap-4">
        <p className="text-sm leading-relaxed">{result.summary}</p>
        {result.score != null && (
          <div className="shrink-0 text-center">
            <div className="text-3xl font-semibold text-accent">{result.score}</div>
            <div className="text-xs text-slate-500">score</div>
          </div>
        )}
      </div>

      {result.recommendations?.length > 0 && (
        <div>
          <h3 className="text-sm font-medium mb-2 text-slate-300">Recommendations</h3>
          <ul className="list-disc pl-5 space-y-1 text-sm text-slate-300">
            {result.recommendations.map((r, i) => (
              <li key={i}>{r}</li>
            ))}
          </ul>
        </div>
      )}

      {result.findings?.length > 0 && (
        <details>
          <summary className="text-sm font-medium cursor-pointer text-slate-300">
            Findings ({result.findings.length})
          </summary>
          <pre className="mt-2 max-h-80 overflow-auto rounded-md bg-ink p-3 text-xs text-slate-400">
            {JSON.stringify(result.findings, null, 2)}
          </pre>
        </details>
      )}

      <details>
        <summary className="text-sm font-medium cursor-pointer text-slate-300">Raw</summary>
        <pre className="mt-2 max-h-80 overflow-auto rounded-md bg-ink p-3 text-xs text-slate-400">
          {JSON.stringify(result.raw, null, 2)}
        </pre>
      </details>
    </div>
  );
}
