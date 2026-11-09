import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "PinForge AI — Autonomous Pinterest Growth Engine",
    short_name: "PinForge",
    description:
      "Transform Amazon product URLs into high-converting 1000x1500 2:3 Pinterest pins in 35ms. Multi-model AI SEO copywriting, FTC-compliant bridge pages, and automated bulk publishing.",
    start_url: "/",
    display: "standalone",
    background_color: "#070A12",
    theme_color: "#070A12",
    icons: [
      {
        src: "/favicon.ico",
        sizes: "any",
        type: "image/x-icon",
      },
    ],
    shortcuts: [
      {
        name: "Pin Studio",
        url: "/",
        description: "Generate 2:3 Pinterest Pins",
      },
      {
        name: "Analytics Suite",
        url: "/analytics",
        description: "View live Pinterest performance ledger",
      },
    ],
  };
}
