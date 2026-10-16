import { NextResponse } from "next/server";

const BASE = process.env.AGENTS_BASE_URL ?? "http://localhost:8000";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const res = await fetch(`${BASE}/providers`, { cache: "no-store" });
    return NextResponse.json(await res.json());
  } catch (e) {
    return NextResponse.json({ error: (e as Error).message }, { status: 502 });
  }
}
