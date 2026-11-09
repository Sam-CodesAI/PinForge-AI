import type { Metadata, Viewport } from "next";
import "./globals.css";

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || "https://pinforge.vercel.app";

export const viewport: Viewport = {
  themeColor: "#070A12",
  colorScheme: "dark",
  width: "device-width",
  initialScale: 1,
};

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: {
    default: "PinForge AI — Autonomous Pinterest & Amazon Affiliate Growth Engine",
    template: "%s | PinForge AI",
  },
  description:
    "Transform Amazon product URLs into high-converting 1000x1500 2:3 Pinterest pins in 35ms. Multi-model AI SEO copywriting, FTC-compliant bridge pages, and automated bulk publishing.",
  applicationName: "PinForge AI",
  keywords: [
    "Pinterest affiliate automation",
    "Amazon Associates workflow",
    "automated pin generator",
    "AI affiliate marketing",
    "Pillow 2:3 graphic engine",
    "Smart Spaces Pinterest",
    "Pixie algorithm optimization",
    "TransAct V2 ranking",
    "passive affiliate income",
    "social commerce automation",
  ],
  authors: [{ name: "Samarth Kallappa Nimangre", url: "https://sam-codes.vercel.app" }],
  creator: "Samarth Kallappa Nimangre",
  publisher: "PinForge AI",
  category: "business",
  alternates: {
    canonical: siteUrl,
    types: {
      "application/rss+xml": `${siteUrl}/feed.xml`,
    },
  },
  openGraph: {
    title: "PinForge AI — Autonomous Pinterest & Amazon Affiliate Growth Engine",
    description:
      "Transform Amazon product URLs into high-converting 1000x1500 2:3 Pinterest pins in 35ms with zero shadowban risk.",
    url: siteUrl,
    siteName: "PinForge AI",
    locale: "en_US",
    type: "website",
    images: [
      {
        url: "/pins/carousel_composite_67e96089.jpg",
        width: 1000,
        height: 1500,
        alt: "PinForge AI — High-Converting 2:3 Pinterest Pin Studio",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "PinForge AI — Autonomous Pinterest & Amazon Affiliate Growth Engine",
    description:
      "Transform Amazon product URLs into high-converting 1000x1500 2:3 Pinterest pins in 35ms with zero shadowban risk.",
    creator: "@Smart_Spaces",
    images: ["/pins/carousel_composite_67e96089.jpg"],
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
  icons: {
    icon: "/favicon.ico",
    shortcut: "/favicon.ico",
  },
  manifest: "/manifest.webmanifest",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const jsonLd = {
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type": "SoftwareApplication",
        "name": "PinForge AI",
        "operatingSystem": "All",
        "applicationCategory": "BusinessApplication",
        "url": siteUrl,
        "description":
          "Autonomous Pinterest & Amazon Affiliate Growth Engine delivering 35ms Pillow 2:3 vertical graphic generation, multi-model AI SEO copywriting, and closed-loop performance ledgers.",
        "offers": {
          "@type": "Offer",
          "price": "0",
          "priceCurrency": "USD",
        },
      },
      {
        "@type": "Organization",
        "name": "PinForge AI",
        "url": siteUrl,
        "logo": `${siteUrl}/favicon.ico`,
        "sameAs": [
          "https://pinterest.com/Smart_Spaces",
          "https://github.com/Sam-CodesAI/PinForge-AI",
        ],
      },
      {
        "@type": "WebSite",
        "name": "PinForge AI",
        "url": siteUrl,
        "potentialAction": {
          "@type": "SearchAction",
          "target": `${siteUrl}/p/{search_term_string}`,
          "query-input": "required name=search_term_string",
        },
      },
    ],
  };

  return (
    <html lang="en" className="dark">
      <head>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
        />
      </head>
      <body className="min-h-screen bg-[#070A12] text-slate-100 antialiased selection:bg-rose-500/30">
        {children}
      </body>
    </html>
  );
}
