import { NextResponse } from "next/server";

const TRANSFER_AI_URL = process.env.TRANSFER_AI_URL || "http://localhost:5001";

export async function POST(req: Request) {
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

    // Stream the SSE response straight through to the browser
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
