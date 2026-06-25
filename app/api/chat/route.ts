import { NextResponse } from "next/server";

export async function POST(req: Request) {
  const TRANSFER_AI_URL = process.env.TRANSFER_AI_URL || "https://course-bridge-ai-production.up.railway.app";
  console.log("[chat] TRANSFER_AI_URL =", TRANSFER_AI_URL);

  try {
    const body = await req.json();

    const upstream = await fetch(`${TRANSFER_AI_URL}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    if (!upstream.ok) {
      return NextResponse.json(
        { error: "Transfer AI service unavailable" },
        { status: 502 }
      );
    }

    return new Response(upstream.body, {
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
      },
    });
  } catch (err) {
    console.error("Chat proxy error:", err);
    return NextResponse.json(
      { error: "Failed to reach Transfer AI service" },
      { status: 502 }
    );
  }
}
