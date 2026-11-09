import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";
import { VERIFIED_PRODUCTS } from "@/data/pinforge-catalog";

interface FeedItem {
  title: string;
  link: string;
  description: string;
  imageUrl: string;
  category: string;
  pubDate: string;
}

interface AutopilotFeedProduct {
  asin?: string;
  title?: string;
  bridge_slug?: string;
}

interface AutopilotFeedEntry {
  timestamp?: string;
  product?: AutopilotFeedProduct;
  seo_copy?: {
    title?: string;
    description?: string;
    board?: string;
  };
}

export async function GET() {
  const baseUrl = process.env.NEXT_PUBLIC_SITE_URL || "https://pinforge.vercel.app";
  const nowUtc = new Date().toUTCString();
  const items: FeedItem[] = [];
  const seenLinks = new Set<string>();

  // 1. Add verified seed catalog products
  for (const prod of Object.values(VERIFIED_PRODUCTS)) {
    const bridgeUrl = `${baseUrl}/p/${prod.slug}`;
    if (!seenLinks.has(bridgeUrl)) {
      seenLinks.add(bridgeUrl);
      items.push({
        title: prod.title,
        link: bridgeUrl,
        description: `${prod.verdict} Rated ${prod.rating} stars with ${prod.reviewCount}. #AmazonAssociate`,
        imageUrl: prod.imageUrl,
        category: prod.boardName,
        pubDate: nowUtc,
      });
    }
  }

  // 2. Ingest autopilot history pins
  try {
    const historyPath = path.join(process.cwd(), "python_engine", "data", "autopilot_history.json");
    if (fs.existsSync(historyPath)) {
      const historyRaw = fs.readFileSync(historyPath, "utf-8");
      const historyData = JSON.parse(historyRaw) as AutopilotFeedEntry[];
      if (Array.isArray(historyData)) {
        for (const entry of historyData.slice(0, 50)) {
          const p = entry.product;
          if (!p) continue;
          const slug = p.bridge_slug || (p.asin ? `amazon-find-${p.asin.toLowerCase()}` : null);
          if (!slug) continue;

          const bridgeUrl = `${baseUrl}/p/${slug}`;
          if (seenLinks.has(bridgeUrl)) continue;
          seenLinks.add(bridgeUrl);

          const title = entry.seo_copy?.title || p.title || "Curated Space Saving Find";
          const desc = entry.seo_copy?.description || "Curated Smart Spaces Amazon Find. #AmazonAssociate";
          const category = entry.seo_copy?.board || "Room Organization";
          const asin = p.asin || "B087F5K713";
          const imgUrl = `https://m.media-amazon.com/images/P/${asin}.01._SCLZZZZZZZ_SX900_.jpg`;
          const pubDate = entry.timestamp ? new Date(entry.timestamp).toUTCString() : nowUtc;

          items.push({
            title,
            link: bridgeUrl,
            description: desc,
            imageUrl: imgUrl,
            category,
            pubDate,
          });
        }
      }
    }
  } catch (err) {
    console.error("Error reading autopilot history for feed.xml:", err);
  }

  let itemsXml = "";
  for (const item of items) {
    const cleanTitle = item.title.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    const cleanDesc = item.description.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    const cleanCategory = item.category.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

    itemsXml += `
    <item>
      <title>${cleanTitle}</title>
      <link>${item.link}</link>
      <description>${cleanDesc}</description>
      <guid isPermaLink="true">${item.link}</guid>
      <enclosure url="${item.imageUrl}" type="image/jpeg" length="100000" />
      <media:content url="${item.imageUrl}" medium="image" type="image/jpeg" />
      <category>${cleanCategory}</category>
      <pubDate>${item.pubDate}</pubDate>
    </item>`;
  }

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>PinForge AI — Curated Amazon Affiliate Finds (@Smart_Spaces)</title>
    <link>${baseUrl}</link>
    <description>Automated high-converting Amazon finds and verified reviews with FTC disclosures.</description>
    <language>en-us</language>
    <pubDate>${nowUtc}</pubDate>
    <atom:link href="${baseUrl}/feed.xml" rel="self" type="application/rss+xml"/>
    ${itemsXml}
  </channel>
</rss>`;

  return new NextResponse(xml, {
    status: 200,
    headers: {
      "Content-Type": "application/rss+xml; charset=utf-8",
      "Cache-Control": "public, s-maxage=3600, stale-while-revalidate=86400",
    },
  });
}
