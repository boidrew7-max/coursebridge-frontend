import { NextResponse } from "next/server";

const TRANSFER_AI_URL = process.env.TRANSFER_AI_URL || "https://course-bridge-ai-production.up.railway.app";

export async function GET(req: Request) {
  const params = new URL(req.url).searchParams;
  const college = params.get("college") || "";
  const uc = params.get("uc") || "";
  try {
    const res = await fetch(
      `${TRANSFER_AI_URL}/api/options/majors?college=${encodeURIComponent(college)}&uc=${encodeURIComponent(uc)}`,
      { next: { revalidate: 3600 } }
    );
    if (!res.ok) return NextResponse.json({ majors: [] }, { status: 502 });
    return NextResponse.json(await res.json());
  } catch {
    return NextResponse.json({ majors: [] }, { status: 502 });
  }
}
