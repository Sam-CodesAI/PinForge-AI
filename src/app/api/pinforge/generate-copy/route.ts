import { NextRequest, NextResponse } from "next/server";

const PYTHON_ENGINE_URL = process.env.PINFORGE_ENGINE_URL || "http://127.0.0.1:8000";
const GEMINI_API_KEY = process.env.GEMINI_API_KEY || "";
const GROQ_API_KEY = process.env.GROQ_API_KEY || "";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { product_title, brand, category, price, features } = body;

    if (!product_title) {
      return NextResponse.json({ error: "Missing product_title" }, { status: 400 });
    }

    // 1. Try Python Engine if reachable
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 2500);
      const res = await fetch(`${PYTHON_ENGINE_URL}/api/generate-copy`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ product_title, brand, category, price, features }),
        signal: controller.signal,
      });
      clearTimeout(timeoutId);

      if (res.ok) {
        const data = await res.json();
        return NextResponse.json(data);
      }
    } catch {
      // Proceed to serverless direct AI call
    }

    // 2. Direct Gemini Call from Next.js Edge / Serverless
    if (GEMINI_API_KEY) {
      try {
        const prompt = `You are an elite Pinterest marketing copywriter.
Generate high-converting Pinterest copy and a bridge review for this Amazon product:
Product: ${product_title}
Brand: ${brand || "Amazon Choice"}
Category: ${category || "Trending Finds"}
Price: ${price || "$29.99"}

REQUIREMENTS:
1. pin_title: STRICTLY UNDER 100 CHARS.
2. pin_description: STRICTLY UNDER 500 CHARS with FTC tag: #AmazonAssociate
3. hashtags: 5-6 Pinterest search tags
4. board_recommendation: 2-4 word Pinterest board name
5. call_to_action: CTA string
6. hook: 4-6 word hook
7. bridge_review: verdict, pros (3 items), cons (1 item), who_is_it_for

Return ONLY valid JSON matching this schema:
{
  "pin_title": "string",
  "pin_description": "string",
  "hashtags": ["#tag1", "#tag2", "#AmazonAssociate"],
  "board_recommendation": "string",
  "call_to_action": "string",
  "hook": "string",
  "bridge_review": {
    "verdict": "string",
    "pros": ["pro 1", "pro 2", "pro 3"],
    "cons": ["con 1"],
    "who_is_it_for": "string"
  }
}`;

        const geminiRes = await fetch(
          `https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-lite-latest:generateContent?key=${GEMINI_API_KEY}`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              contents: [{ parts: [{ text: prompt }] }],
            }),
          }
        );

        if (geminiRes.ok) {
          const gemData = await geminiRes.json();
          const rawText = gemData.candidates?.[0]?.content?.parts?.[0]?.text || "";
          const cleanJson = rawText.replace(/```(?:json)?/g, "").replace(/```/g, "").trim();
          const parsed = JSON.parse(cleanJson);

          let pin_desc = parsed.pin_description || "";
          if (!pin_desc.includes("#AmazonAssociate")) {
            pin_desc = (pin_desc.slice(0, 480) + " #AmazonAssociate").slice(0, 500);
          }

          return NextResponse.json({
            pin_title: (parsed.pin_title || product_title).slice(0, 100),
            pin_description: pin_desc,
            hashtags: parsed.hashtags || ["#AmazonFinds", "#Trending", "#AmazonAssociate"],
            board_recommendation: parsed.board_recommendation || (category || "Trending Finds"),
            call_to_action: parsed.call_to_action || "Tap to check today's price & details!",
            hook: parsed.hook || "The Viral Amazon Find You Need",
            bridge_review: parsed.bridge_review || {
              verdict: "A verified top-tier product delivering exceptional everyday utility.",
              pros: ["Superb design", "Verified durability", "Prime fast shipping"],
              cons: ["High demand may lead to temporary backorders"],
              who_is_it_for: "Anyone looking for a reliable, premium quality upgrade.",
            },
          });
        }
      } catch {
        // Fallback to rules below
      }
    }

    // 3. Deterministic Rule Fallback
    const title = `Why Everyone Is Obsessed With The ${product_title}`.slice(0, 95);
    const desc = `Looking for the best ${(category || "lifestyle").toLowerCase()} upgrade? The ${product_title} delivers verified customer ratings, outstanding build quality, and sleek aesthetics. Tap to check today's live deal! #AmazonFinds #Trending #AmazonAssociate`.slice(0, 495);

    return NextResponse.json({
      pin_title: title,
      pin_description: desc,
      hashtags: ["#AmazonFinds", "#ViralFinds", "#MustHaves", "#AmazonAssociate"],
      board_recommendation: `${category || "Lifestyle"} Finds`,
      call_to_action: "Tap to check today's deal on Amazon ➔",
      hook: "The Viral Amazon Find You Need",
      bridge_review: {
        verdict: "One of the most requested and highly rated finds in its class.",
        pros: [
          "Consistently high customer ratings across thousands of purchases",
          "Engineered for durable everyday use and premium ergonomics",
          "Eligible for fast Prime delivery and hassle-free returns",
        ],
        cons: ["Stock sells out quickly during peak promotional sales"],
        who_is_it_for: "Anyone seeking a dependable, high-performance upgrade.",
      },
    });
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : "Internal Server Error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
