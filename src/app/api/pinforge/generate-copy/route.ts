import { NextRequest, NextResponse } from "next/server";

const PYTHON_ENGINE_URL = process.env.PINFORGE_ENGINE_URL || "http://127.0.0.1:8000";
const GEMINI_API_KEY = process.env.GEMINI_API_KEY || "";
const GROQ_API_KEY = process.env.GROQ_API_KEY || "";

const OFFICIAL_BOARDS = [
  "Small Apartment Hacks",
  "Space Saving Kitchens",
  "Closet & Wardrobe Organization",
  "Studio Living Ideas",
  "Room Organization",
] as const;

function matchOfficialBoard(suggested?: string, context?: string): string {
  const s = (suggested || "").trim();
  for (const b of OFFICIAL_BOARDS) {
    if (b.toLowerCase() === s.toLowerCase()) {
      return b;
    }
  }
  const combined = `${suggested || ""} ${context || ""}`.toLowerCase();
  if (
    combined.includes("kitchen") ||
    combined.includes("spice") ||
    combined.includes("pantry") ||
    combined.includes("dish") ||
    combined.includes("cabinet")
  ) {
    return "Space Saving Kitchens";
  }
  if (
    combined.includes("closet") ||
    combined.includes("wardrobe") ||
    combined.includes("hanger") ||
    combined.includes("clothes") ||
    combined.includes("drawer")
  ) {
    return "Closet & Wardrobe Organization";
  }
  if (
    combined.includes("studio") ||
    combined.includes("divider") ||
    combined.includes("multi-function") ||
    combined.includes("compact living")
  ) {
    return "Studio Living Ideas";
  }
  if (
    combined.includes("apartment") ||
    combined.includes("renter") ||
    combined.includes("no drill") ||
    combined.includes("foldable") ||
    combined.includes("hack")
  ) {
    return "Small Apartment Hacks";
  }
  return "Room Organization";
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { product_title, brand, category, price, features } = body;

    if (!product_title) {
      return NextResponse.json({ error: "Missing product_title" }, { status: 400 });
    }

    const contextStr = `${product_title} ${category || ""} ${brand || ""}`;

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
        data.board_recommendation = matchOfficialBoard(data.board_recommendation, contextStr);
        return NextResponse.json(data);
      }
    } catch {
      // Proceed to direct Groq / Gemini call
    }

    // 2. Direct Groq API Call if GROQ_API_KEY is configured
    if (GROQ_API_KEY) {
      const groqModels = ["qwen/qwen3.8-27b", "openai/gpt-oss-120b", "openai/gpt-oss-20b"];
      const prompt = `You are an elite Pinterest marketing copywriter for Pinterest profile @Smart_Spaces.
Generate high-converting Pinterest copy and a bridge review for this space-saving Amazon product:
Product: ${product_title}
Brand: ${brand || "Amazon Choice"}
Category: ${category || "Home Organization"}
Price: ${price || "$29.99"}

CRITICAL CONSTRAINTS:
1. pin_title: STRICTLY UNDER 100 CHARACTERS. No markdown asterisks, emojis, or quotes. High CTR viral hook.
2. pin_description: STRICTLY UNDER 500 CHARACTERS. Must end with #AmazonAssociate.
3. hashtags: 5-6 Pinterest search tags including #AmazonAssociate.
4. board_recommendation: MUST BE EXACTLY ONE of these 5 official @Smart_Spaces boards:
   - "Small Apartment Hacks"
   - "Space Saving Kitchens"
   - "Closet & Wardrobe Organization"
   - "Studio Living Ideas"
   - "Room Organization"
5. call_to_action: Direct, compelling action phrase.
6. hook: 4-6 word punchy hook.
7. bridge_review: verdict, pros (3 items), cons (1 item), who_is_it_for.

Return ONLY valid JSON matching this schema:
{
  "pin_title": "string",
  "pin_description": "string",
  "hashtags": ["#tag1", "#tag2", "#AmazonAssociate"],
  "board_recommendation": "Small Apartment Hacks",
  "call_to_action": "string",
  "hook": "string",
  "bridge_review": {
    "verdict": "string",
    "pros": ["pro 1", "pro 2", "pro 3"],
    "cons": ["con 1"],
    "who_is_it_for": "string"
  }
}`;

      for (const model of groqModels) {
        try {
          const groqRes = await fetch("https://api.groq.com/openai/v1/chat/completions", {
            method: "POST",
            headers: {
              "Authorization": `Bearer ${GROQ_API_KEY}`,
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              model,
              messages: [
                {
                  role: "system",
                  content: "You are an expert Pinterest copywriter who outputs ONLY strict JSON.",
                },
                {
                  role: "user",
                  content: prompt,
                },
              ],
              response_format: { type: "json_object" },
              temperature: 0.6,
            }),
          });

          if (groqRes.ok) {
            const groqData = await groqRes.json();
            const rawContent = groqData.choices?.[0]?.message?.content || "";
            const parsed = JSON.parse(rawContent);

            let pin_desc = parsed.pin_description || "";
            if (!pin_desc.includes("#AmazonAssociate")) {
              pin_desc = (pin_desc.slice(0, 480) + " #AmazonAssociate").slice(0, 500);
            }

            const board = matchOfficialBoard(parsed.board_recommendation, contextStr);

            return NextResponse.json({
              pin_title: (parsed.pin_title || product_title).slice(0, 100),
              pin_description: pin_desc,
              hashtags: parsed.hashtags || ["#SmallSpaceHacks", "#HomeOrganization", "#AmazonAssociate"],
              board_recommendation: board,
              call_to_action: parsed.call_to_action || "Tap to check today's price & details!",
              hook: parsed.hook || "The Viral Space-Saving Find",
              bridge_review: parsed.bridge_review || {
                verdict: "A verified top-tier space-saving find delivering exceptional everyday utility.",
                pros: ["Superb design", "Verified durability", "Prime fast shipping"],
                cons: ["High demand may lead to temporary backorders"],
                who_is_it_for: "Apartment dwellers and minimalists looking to maximize living space.",
              },
            });
          }
        } catch {
          continue;
        }
      }
    }

    // 3. Direct Gemini Call from Next.js Serverless
    if (GEMINI_API_KEY) {
      try {
        const prompt = `You are an elite Pinterest marketing copywriter for Pinterest profile @Smart_Spaces.
Generate high-converting Pinterest copy and a bridge review for this space-saving Amazon product:
Product: ${product_title}
Brand: ${brand || "Amazon Choice"}
Category: ${category || "Home Organization"}
Price: ${price || "$29.99"}

CRITICAL CONSTRAINTS:
1. pin_title: STRICTLY UNDER 100 CHARS.
2. pin_description: STRICTLY UNDER 500 CHARS with FTC tag: #AmazonAssociate
3. hashtags: 5-6 Pinterest search tags
4. board_recommendation: MUST BE EXACTLY ONE of:
   - "Small Apartment Hacks"
   - "Space Saving Kitchens"
   - "Closet & Wardrobe Organization"
   - "Studio Living Ideas"
   - "Room Organization"
5. call_to_action: CTA string
6. hook: 4-6 word hook
7. bridge_review: verdict, pros (3 items), cons (1 item), who_is_it_for

Return ONLY valid JSON matching this schema:
{
  "pin_title": "string",
  "pin_description": "string",
  "hashtags": ["#tag1", "#tag2", "#AmazonAssociate"],
  "board_recommendation": "Small Apartment Hacks",
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

          const board = matchOfficialBoard(parsed.board_recommendation, contextStr);

          return NextResponse.json({
            pin_title: (parsed.pin_title || product_title).slice(0, 100),
            pin_description: pin_desc,
            hashtags: parsed.hashtags || ["#SmallSpaceHacks", "#HomeOrganization", "#AmazonAssociate"],
            board_recommendation: board,
            call_to_action: parsed.call_to_action || "Tap to check today's price & details!",
            hook: parsed.hook || "The Viral Space-Saving Find",
            bridge_review: parsed.bridge_review || {
              verdict: "A verified top-tier space-saving product delivering exceptional everyday utility.",
              pros: ["Superb design", "Verified durability", "Prime fast shipping"],
              cons: ["High demand may lead to temporary backorders"],
              who_is_it_for: "Apartment dwellers looking for a reliable, compact upgrade.",
            },
          });
        }
      } catch {
        // Fallback to rules below
      }
    }

    // 4. Deterministic Rule Fallback
    const board = matchOfficialBoard(category, contextStr);
    const title = `Why Everyone Is Obsessed With The ${product_title}`.slice(0, 95);
    const desc = `Looking for the best compact apartment upgrade? The ${product_title} delivers verified customer ratings, outstanding build quality, and sleek space-saving utility. Tap to check today's live deal! #SmallApartmentHacks #SmartSpaces #AmazonAssociate`.slice(0, 495);

    return NextResponse.json({
      pin_title: title,
      pin_description: desc,
      hashtags: ["#SmallApartmentHacks", "#SmartSpaces", "#AmazonFinds", "#AmazonAssociate"],
      board_recommendation: board,
      call_to_action: "Tap to check today's deal on Amazon ➔",
      hook: "Space-Saving Apartment Genius",
      bridge_review: {
        verdict: "One of the most requested and highly rated finds for compact apartment living.",
        pros: [
          "Consistently high customer ratings across thousands of purchases",
          "Engineered for durable everyday space-saving utility",
          "Eligible for fast Prime delivery and hassle-free returns",
        ],
        cons: ["Stock sells out quickly during peak promotional sales"],
        who_is_it_for: "Anyone seeking to maximize compact living space and eliminate clutter.",
      },
    });
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : "Internal Server Error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
