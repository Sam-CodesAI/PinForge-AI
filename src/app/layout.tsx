import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PinForge AI — Autonomous Pinterest & Amazon Affiliate Growth Engine",
  description:
    "Transform Amazon product URLs into high-converting 1000x1500 2:3 Pinterest pins in 35ms. Multi-model AI SEO copywriting, FTC-compliant bridge pages, and automated bulk publishing.",
  keywords: [
    "Pinterest affiliate automation",
    "Amazon Associates workflow",
    "automated pin generator",
    "AI affiliate marketing",
    "Pillow 2:3 graphic engine",
  ],
  authors: [{ name: "Samarth Kallappa Nimangre (SAM CODES)", url: "https://sam-codes.vercel.app" }],
  openGraph: {
    title: "PinForge AI — Autonomous Pinterest & Amazon Affiliate Growth Engine",
    description:
      "Transform Amazon product URLs into high-converting 1000x1500 2:3 Pinterest pins in 35ms with zero shadowban risk.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-[#070A12] text-slate-100 antialiased selection:bg-rose-500/30">
        {children}
      </body>
    </html>
  );
}
