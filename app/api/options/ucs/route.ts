import { NextResponse } from "next/server";

const TRANSFER_AI_URL = process.env.TRANSFER_AI_URL || "https://course-bridge-ai-production.up.railway.app";

export async function GET(req: Request) {
  const college = new URL(req.url).searchParams.get("college") || "";
  try {
    const res = await fetch(`${TRANSFER_AI_URL}/api/options/ucs?college=${encodeURIComponent(college)}`, { next: { revalidate: 3600 } });
    if (!res.ok) return NextResponse.json({ ucs: [] }, { status: 502 });
    return NextResponse.json(await res.json());
  } catch {
    return NextResponse.json({ ucs: [] }, { status: 502 });
  }
}
