import { NextResponse } from "next/server";

const TRANSFER_AI_URL = process.env.TRANSFER_AI_URL || "https://course-bridge-ai-production.up.railway.app";

export async function GET() {
  try {
    const res = await fetch(`${TRANSFER_AI_URL}/api/options/colleges`, { next: { revalidate: 3600 } });
    if (!res.ok) return NextResponse.json({ colleges: [] }, { status: 502 });
    return NextResponse.json(await res.json());
  } catch {
    return NextResponse.json({ colleges: [] }, { status: 502 });
  }
}
