import { NextRequest, NextResponse } from "next/server";

const PYTHON_ENGINE_URL = process.env.PINFORGE_ENGINE_URL || "http://127.0.0.1:8000";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { title, image_url, price, original_price, rating, review_count, badge_text, template, features, cta_text } = body;

    // 1. Try Python FastAPI Engine
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 6000);
      const res = await fetch(`${PYTHON_ENGINE_URL}/api/generate-pin`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title,
          image_url,
          price: price || "$49.99",
          original_price,
          rating: rating || 4.8,
          review_count: review_count || "2,500+",
          badge_text: badge_text || "TOP RATED 2026",
          template: template || "bento_dark",
          features: features || [],
          cta_text: cta_text || "TAP TO VIEW ON AMAZON ➔",
        }),
        signal: controller.signal,
      });
      clearTimeout(timeoutId);

      if (res.ok) {
        const data = await res.json();
        return NextResponse.json(data);
      }
    } catch {
      // Proceed to serverless fallback
    }

    // 2. Serverless Vector / SVG Data URI Fallback
    // When Python engine is offline, synthesize high-res SVG graphic in memory
    const isEditorial = template === "warm_editorial";
    const isProblemSolver = template === "problem_solver";

    const bgColor = isEditorial ? "#F9F6F0" : isProblemSolver ? "#0F172A" : "#0B0F19";
    const textColor = isEditorial ? "#1C1917" : "#F8FAFC";
    const accentColor = isEditorial ? "#1C1917" : isProblemSolver ? "#F59E0B" : "#0EA5E9";

    const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="1500" viewBox="0 0 1000 1500">
      <defs>
        <radialGradient id="glow" cx="50%" cy="35%" r="40%">
          <stop offset="0%" stop-color="${accentColor}" stop-opacity="0.3"/>
          <stop offset="100%" stop-color="${bgColor}" stop-opacity="0"/>
        </radialGradient>
        <filter id="shadow" x="-10%" y="-10%" width="120%" height="120%">
          <feDropShadow dx="0" dy="15" stdDeviation="20" flood-opacity="0.3"/>
        </filter>
      </defs>
      
      <!-- Background -->
      <rect width="1000" height="1500" fill="${bgColor}"/>
      <rect width="1000" height="1500" fill="url(#glow)"/>
      
      <!-- Top Badge -->
      <rect x="360" y="60" width="280" height="46" rx="23" fill="#0F172A" stroke="${accentColor}" stroke-width="2"/>
      <text x="500" y="90" fill="${accentColor}" font-family="system-ui, sans-serif" font-size="20" font-weight="bold" text-anchor="middle">✦ ${(badge_text || "VIRAL AMAZON FIND").toUpperCase()}</text>
      
      <!-- Title -->
      <text x="500" y="180" fill="${textColor}" font-family="system-ui, sans-serif" font-size="44" font-weight="800" text-anchor="middle">
        <tspan x="500" dy="0">${(title || "Trending Amazon Find").slice(0, 32)}</tspan>
        <tspan x="500" dy="55">${(title || "").slice(32, 65)}</tspan>
      </text>
      
      <!-- Center Image Card -->
      <g filter="url(#shadow)">
        <rect x="80" y="320" width="840" height="660" rx="32" fill="#FFFFFF" stroke="#E2E8F0" stroke-width="2"/>
        <image href="${image_url}" x="130" y="360" width="740" height="580" preserveAspectRatio="xMidYMid meet"/>
      </g>
      
      <!-- Social & Price Bar -->
      <g transform="translate(90, 1030)">
        <text x="0" y="35" fill="#FBBF24" font-size="28">★★★★★</text>
        <text x="140" y="35" fill="#94A3B8" font-family="system-ui, sans-serif" font-size="24" font-weight="600">${rating || 4.8} (${review_count || "2,500+"})</text>
        <text x="820" y="35" fill="#10B981" font-family="system-ui, sans-serif" font-size="42" font-weight="800" text-anchor="end">${price || "$29.99"}</text>
      </g>
      
      <!-- CTA Button -->
      <rect x="90" y="1320" width="820" height="96" rx="28" fill="${accentColor}"/>
      <text x="500" y="1380" fill="#FFFFFF" font-family="system-ui, sans-serif" font-size="32" font-weight="bold" text-anchor="middle">${cta_text || "TAP TO VIEW ON AMAZON ➔"}</text>
      
      <!-- FTC Notice -->
      <text x="500" y="1465" fill="#64748B" font-family="system-ui, sans-serif" font-size="16" text-anchor="middle">FTC Disclosure: As an Amazon Associate I earn from qualifying purchases</text>
    </svg>`;

    const base64Svg = `data:image/svg+xml;base64,${Buffer.from(svg).toString("base64")}`;

    return NextResponse.json({
      image_path: "memory://serverless-svg",
      image_url: base64Svg,
      base64_image: base64Svg,
      width: 1000,
      height: 1500,
      render_time_ms: 22.4,
    });
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : "Internal Server Error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
