import type { MetadataRoute } from "next";
import fs from "fs";
import path from "path";
import { VERIFIED_PRODUCTS } from "@/data/pinforge-catalog";

interface AutopilotProduct {
  asin?: string;
  bridge_slug?: string;
}

interface AutopilotEntry {
  timestamp?: string;
  product?: AutopilotProduct;
}

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const baseUrl = process.env.NEXT_PUBLIC_SITE_URL || "https://pinforge.vercel.app";
  const now = new Date();

  const entries: MetadataRoute.Sitemap = [
    {
      url: baseUrl,
      lastModified: now,
      changeFrequency: "daily",
      priority: 1.0,
    },
    {
      url: `${baseUrl}/analytics`,
      lastModified: now,
      changeFrequency: "daily",
      priority: 0.9,
    },
    {
      url: `${baseUrl}/feed.xml`,
      lastModified: now,
      changeFrequency: "daily",
      priority: 0.8,
    },
  ];

  const seenSlugs = new Set<string>();

  // 1. Add verified seed catalog products
  for (const prod of Object.values(VERIFIED_PRODUCTS)) {
    if (!seenSlugs.has(prod.slug)) {
      seenSlugs.add(prod.slug);
      entries.push({
        url: `${baseUrl}/p/${prod.slug}`,
        lastModified: now,
        changeFrequency: "weekly",
        priority: 0.8,
      });
    }
  }

  // 2. Add all unique discovered products from autopilot history
  try {
    const historyPath = path.join(process.cwd(), "python_engine", "data", "autopilot_history.json");
    if (fs.existsSync(historyPath)) {
      const historyRaw = fs.readFileSync(historyPath, "utf-8");
      const historyData = JSON.parse(historyRaw) as AutopilotEntry[];
      if (Array.isArray(historyData)) {
        for (const item of historyData) {
          const p = item.product;
          if (!p) continue;
          const slug = p.bridge_slug || (p.asin ? `amazon-find-${p.asin.toLowerCase()}` : null);
          if (slug && !seenSlugs.has(slug)) {
            seenSlugs.add(slug);
            const pubDate = item.timestamp ? new Date(item.timestamp) : now;
            entries.push({
              url: `${baseUrl}/p/${slug}`,
              lastModified: isNaN(pubDate.getTime()) ? now : pubDate,
              changeFrequency: "weekly",
              priority: 0.7,
            });
          }
        }
      }
    }
  } catch (err) {
    console.error("Error reading autopilot history for sitemap:", err);
  }

  return entries;
}
