import { NextRequest, NextResponse } from "next/server";
import { runAgent } from "@/lib/agents";
import { prisma } from "@/lib/db";

export const dynamic = "force-dynamic";
export const maxDuration = 300; // agent runs do live scraping + LLM calls

export async function POST(req: NextRequest) {
  const body = await req.json().catch(() => null);
  if (!body?.agent || typeof body.input !== "object") {
    return NextResponse.json({ error: "Expected { agent, input }" }, { status: 400 });
  }

  try {
    const result = await runAgent(body.agent, body.input);

    // Persist the run (best-effort — don't fail the request if the DB is down).
    let runId: string | null = null;
    try {
      const row = await prisma.run.create({
        data: {
          agent: body.agent,
          input: body.input,
          status: "completed",
          summary: result.summary,
          score: result.score ?? undefined,
          findings: result.findings as object,
          recommendations: result.recommendations as object,
          raw: result.raw as object,
          finishedAt: new Date(),
        },
      });
      runId = row.id;
    } catch {
      // DB not configured/available — results still returned to the client.
    }

    return NextResponse.json({ runId, result });
  } catch (e) {
    return NextResponse.json({ error: (e as Error).message }, { status: 502 });
  }
}
