import type { MetadataRoute } from "next";

export default function robots(): MetadataRoute.Robots {
  const baseUrl = process.env.NEXT_PUBLIC_SITE_URL || "https://pinforge.vercel.app";

  return {
    rules: [
      {
        userAgent: "*",
        allow: ["/", "/p/", "/analytics", "/feed.xml"],
        disallow: ["/api/"],
      },
      {
        userAgent: "Pinterestbot",
        allow: ["/", "/p/", "/analytics", "/feed.xml", "/pins/"],
      },
    ],
    sitemap: `${baseUrl}/sitemap.xml`,
  };
}
