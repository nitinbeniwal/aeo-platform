import { prisma } from "@/lib/db";

export const dynamic = "force-dynamic";

async function getRuns() {
  try {
    return await prisma.run.findMany({
      orderBy: { createdAt: "desc" },
      take: 50,
      select: { id: true, agent: true, summary: true, score: true, createdAt: true },
    });
  } catch {
    return [];
  }
}

export default async function HistoryPage() {
  const runs = await getRuns();
  return (
    <>
      <h1 className="text-2xl font-semibold mb-6">Run history</h1>
      {runs.length === 0 ? (
        <p className="text-slate-400">
          No runs yet (or the database isn&apos;t configured). Runs appear here once DATABASE_URL is set.
        </p>
      ) : (
        <div className="space-y-3">
          {runs.map((r) => (
            <div key={r.id} className="rounded-xl border border-white/10 bg-panel p-4">
              <div className="flex items-center justify-between">
                <span className="text-xs uppercase tracking-wide text-accent">{r.agent}</span>
                <span className="text-xs text-slate-500">
                  {new Date(r.createdAt).toLocaleString()}
                </span>
              </div>
              <p className="text-sm mt-1">{r.summary}</p>
              {r.score != null && (
                <span className="text-xs text-slate-400">score {r.score}</span>
              )}
            </div>
          ))}
        </div>
      )}
    </>
  );
}
