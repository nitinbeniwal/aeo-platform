import { NextResponse } from "next/server";
import { listAgents } from "@/lib/agents";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const agents = await listAgents();
    return NextResponse.json(agents);
  } catch (e) {
    return NextResponse.json(
      { error: (e as Error).message, hint: "Is the agents service running on AGENTS_BASE_URL?" },
      { status: 502 }
    );
  }
}
