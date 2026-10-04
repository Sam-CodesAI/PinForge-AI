import { NextResponse } from "next/server";
import { VERIFIED_PRODUCTS } from "@/data/pinforge-catalog";

export async function GET() {
  const baseUrl = process.env.NEXT_PUBLIC_SITE_URL || "https://sam-codes.vercel.app";
  const nowUtc = new Date().toUTCString();

  let itemsXml = "";
  for (const prod of Object.values(VERIFIED_PRODUCTS)) {
    const bridgeUrl = `${baseUrl}/p/${prod.slug}`;
    const cleanTitle = prod.title.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    const cleanDesc = `${prod.verdict} Rated ${prod.rating} stars with ${prod.reviewCount}. #AmazonAssociate`
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");

    itemsXml += `
    <item>
      <title>${cleanTitle}</title>
      <link>${bridgeUrl}</link>
      <description>${cleanDesc}</description>
      <guid isPermaLink="true">${bridgeUrl}</guid>
      <enclosure url="${prod.imageUrl}" type="image/jpeg" length="100000" />
      <media:content url="${prod.imageUrl}" medium="image" type="image/jpeg" />
      <category>${prod.boardName}</category>
      <pubDate>${nowUtc}</pubDate>
    </item>`;
  }

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>PinForge AI — Curated Amazon Affiliate Finds</title>
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
