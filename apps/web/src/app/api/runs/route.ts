import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const runs = await prisma.run.findMany({
      orderBy: { createdAt: "desc" },
      take: 25,
      select: { id: true, agent: true, summary: true, score: true, createdAt: true },
    });
    return NextResponse.json(runs);
  } catch {
    return NextResponse.json([]); // DB optional
  }
}
