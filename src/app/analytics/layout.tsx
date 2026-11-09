import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Pinterest Performance Analytics & Live Ledger",
  description:
    "Live Pinterest API v5 business intelligence dashboard for @Smart_Spaces. Monitor Algorithmic Engagement Score (AES), pin CTRs, outbound conversions, and save multiplier diagnostics.",
  alternates: {
    canonical: "/analytics",
  },
  openGraph: {
    title: "Smart Spaces — Live Pinterest Analytics & Ledger",
    description:
      "Track Algorithmic Engagement Score (AES), outbound conversion winners, and Pixie graph diagnostics for @Smart_Spaces.",
    url: "/analytics",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Smart Spaces — Live Pinterest Analytics & Ledger",
    description:
      "Track Algorithmic Engagement Score (AES), outbound conversion winners, and Pixie graph diagnostics for @Smart_Spaces.",
    creator: "@Smart_Spaces",
  },
};

export default function AnalyticsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
