/**
 * PinForge AI — Verified Seed Catalog & Product Store
 * High-converting Amazon products ready for immediate 1-click generation and bridge pages.
 */

export interface CatalogProduct {
  asin: string;
  slug: string;
  title: string;
  shortTitle: string;
  brand: string;
  category: string;
  boardName: string;
  price: string;
  originalPrice?: string;
  discountPercent?: number;
  rating: number;
  reviewCount: string;
  imageUrl: string;
  additionalImages: string[];
  features: string[];
  verdict: string;
  pros: string[];
  cons: string[];
  whoIsItFor: string;
  hook: string;
  hashtags: string[];
}

export const VERIFIED_PRODUCTS: Record<string, CatalogProduct> = {
  "sony-wh-1000xm5": {
    asin: "B09XS7JWHH",
    slug: "sony-wh-1000xm5",
    title: "Sony WH-1000XM5 Wireless Industry Leading Noise Canceling Headphones",
    shortTitle: "Sony WH-1000XM5 Headphones",
    brand: "Sony",
    category: "Tech & Audio",
    boardName: "Must-Have Tech Gadgets",
    price: "$348.00",
    originalPrice: "$399.99",
    discountPercent: 13,
    rating: 4.6,
    reviewCount: "24,850+ ratings",
    imageUrl: "https://m.media-amazon.com/images/P/B09XS7JWHH.01._SCLZZZZZZZ_SX900_.jpg",
    additionalImages: [
      "https://m.media-amazon.com/images/P/B09XS7JWHH.01._SCLZZZZZZZ_SX900_.jpg",
    ],
    features: [
      "Auto NC Optimizer automatically tailors noise cancellation to your ambient environment",
      "Up to 30-hour battery life with ultra-fast 3-minute charge providing 3 hours of playback",
      "Ultra-comfortable, lightweight 250g chassis crafted with soft-fit synthetic leather",
      "8-microphone array engineered for unmatched voice isolation and crystal-clear calls",
    ],
    verdict: "The undisputed gold standard in wireless active noise cancellation for commuters, travelers, and remote workers.",
    pros: [
      "World-class active noise cancellation that silences airplane rumble and office chatter",
      "Exceptionally lightweight design eliminates crown pressure during 8+ hour work sessions",
      "Flawless multipoint Bluetooth switching between laptop and smartphone",
    ],
    cons: [
      "Non-folding headband takes up slightly more space in travel bags than the older XM4",
    ],
    whoIsItFor: "Remote professionals, daily commuters, and frequent flyers seeking maximum acoustic isolation and luxury comfort.",
    hook: "The Ultimate Noise-Canceling Upgrade",
    hashtags: ["#SonyWH1000XM5", "#TechGadgets", "#WorkFromHome", "#AestheticDesk", "#AmazonAssociate"],
  },
  "kindle-paperwhite": {
    asin: "B09SWW583J",
    slug: "kindle-paperwhite",
    title: "Kindle Paperwhite (16 GB) – 6.8\" Glare-Free Display with Adjustable Warm Light",
    shortTitle: "Kindle Paperwhite 16GB",
    brand: "Amazon",
    category: "Books & E-Readers",
    boardName: "Booktok & Cozy Reading",
    price: "$149.99",
    originalPrice: "$169.99",
    discountPercent: 12,
    rating: 4.7,
    reviewCount: "48,900+ ratings",
    imageUrl: "https://m.media-amazon.com/images/P/B09SWW583J.01._SCLZZZZZZZ_SX900_.jpg",
    additionalImages: [],
    features: [
      "Purpose-built 6.8\" flush-front display with 300 ppi glare-free paper-like reading",
      "Adjustable warm light shifts screen tone from crisp white to soothing amber",
      "Up to 10 weeks of battery life on a single USB-C charge",
      "IPX8 waterproof rated to protect against accidental submersion in bath or pool",
    ],
    verdict: "The quintessential modern reading device, blending laser-crisp e-ink with weeks of battery and total water resistance.",
    pros: [
      "Zero screen glare even in direct noon sunlight",
      "Warm backlight mode virtually eliminates eye strain during late-night reading",
      "Astonishing 10-week battery life means you rarely think about charging",
    ],
    cons: [
      "Black-and-white e-ink only; not intended for full-color graphic novels",
    ],
    whoIsItFor: "Book lovers, students, and travelers wanting an entire library in a pocketable, distraction-free slab.",
    hook: "Your Entire Library Anywhere You Go",
    hashtags: ["#KindlePaperwhite", "#BookTok", "#ReadingCommunity", "#AmazonMustHaves", "#AmazonAssociate"],
  },
  "stanley-quencher-40oz": {
    asin: "B0BYP6DZ53",
    slug: "stanley-quencher-40oz",
    title: "Stanley Quencher H2.0 FlowState Stainless Steel Insulated Tumbler 40oz",
    shortTitle: "Stanley Quencher 40oz Tumbler",
    brand: "Stanley",
    category: "Kitchen & Hydration",
    boardName: "Everyday Aesthetic Essentials",
    price: "$45.00",
    originalPrice: "$50.00",
    discountPercent: 10,
    rating: 4.8,
    reviewCount: "32,150+ ratings",
    imageUrl: "https://m.media-amazon.com/images/P/B0BYP6DZ53.01._SCLZZZZZZZ_SX900_.jpg",
    additionalImages: [],
    features: [
      "Double-wall vacuum insulation keeps ice frozen for 48 hours or drinks cold for 11 hours",
      "3-position FlowState rotating lid: reusable straw port, drinking spout, and full cover seal",
      "Tapered slim base engineered to fit smoothly into standard automotive cup holders",
      "Ergonomic comfort-grip handle for effortless transport to gym, office, or campus",
    ],
    verdict: "The viral hydration icon that actually lives up to the hype with unbeatable ice retention and car cup holder fit.",
    pros: [
      "Genuinely keeps ice solid for two full days without sweating",
      "Narrow bottom base fits all standard car cup holders despite huge 40oz capacity",
      "Dishwasher safe stainless steel construction cleans up in minutes",
    ],
    cons: [
      "Heavier than plastic water bottles when filled to brim with 40oz of liquid",
    ],
    whoIsItFor: "Anyone aiming to hit daily hydration goals with aesthetic, durable, ice-cold drinks on the move.",
    hook: "The Viral Cup That Lives Up To The Hype",
    hashtags: ["#StanleyCup", "#StanleyQuencher", "#HydrationGoals", "#AestheticVibes", "#AmazonAssociate"],
  },
  "nespresso-vertuo-plus": {
    asin: "B08C1W5N87",
    slug: "nespresso-vertuo-plus",
    title: "Nespresso Vertuo Plus Coffee and Espresso Machine by De'Longhi",
    shortTitle: "Nespresso Vertuo Plus",
    brand: "Nespresso",
    category: "Kitchen & Coffee Bar",
    boardName: "Home Barista & Coffee Bar",
    price: "$129.95",
    originalPrice: "$169.00",
    discountPercent: 23,
    rating: 4.6,
    reviewCount: "15,840+ ratings",
    imageUrl: "https://m.media-amazon.com/images/P/B08C1W5N87.01._SCLZZZZZZZ_SX900_.jpg",
    additionalImages: [],
    features: [
      "Patented Centrifusion technology spins capsules at 7,000 RPM for velvet-smooth crema",
      "Smart laser barcode reader automatically adjusts water volume, temperature, and flow",
      "Brews 5 distinct beverage sizes ranging from 1.35oz single espresso up to 14oz Alto",
      "Motorized one-touch opening head and movable 60oz water reservoir",
    ],
    verdict: "Brings cafe-quality barista espresso and rich foam into your kitchen at the single push of a button.",
    pros: [
      "Incredible thick, velvety crema on every single cup without manual tamping",
      "Heats up in just 20 seconds for instant morning coffee",
      "Flexible water tank can swivel to the side or back to fit tight countertop corners",
    ],
    cons: [
      "Requires Vertuo-specific barcode capsules rather than original Nespresso pods",
    ],
    whoIsItFor: "Coffee enthusiasts wanting luxury European espresso and rich coffee without buying a complex manual machine.",
    hook: "Cafe-Quality Crema in 20 Seconds",
    hashtags: ["#NespressoVertuo", "#CoffeeBar", "#MorningRoutine", "#KitchenFinds", "#AmazonAssociate"],
  },
  "macbook-pro-m2": {
    asin: "B0BSHF7WHW",
    slug: "macbook-pro-m2",
    title: "Apple 2023 MacBook Pro Laptop with Apple M2 Pro Chip (14-inch, Liquid Retina XDR)",
    shortTitle: "Apple MacBook Pro 14-inch",
    brand: "Apple",
    category: "Laptops & Computing",
    boardName: "Dream Desk Setup & Tech",
    price: "$1,799.00",
    originalPrice: "$1,999.00",
    discountPercent: 10,
    rating: 4.8,
    reviewCount: "3,420+ ratings",
    imageUrl: "https://m.media-amazon.com/images/P/B0BSHF7WHW.01._SCLZZZZZZZ_SX900_.jpg",
    additionalImages: [],
    features: [
      "M2 Pro chip delivers blazing performance with 10-core CPU and 16-core GPU",
      "14.2-inch Liquid Retina XDR display with 1,000 nits sustained full-screen brightness",
      "Up to 18 hours of real-world battery life on a single charge",
      "Full port suite: MagSafe 3, 3x Thunderbolt 4, HDMI port, and SDXC card slot",
    ],
    verdict: "The definitive workstation for software developers, 4K video editors, and creative power users.",
    pros: [
      "Phenomenal Liquid Retina XDR screen with deep OLED-like blacks and 120Hz ProMotion",
      "Stays completely silent and cool even under heavy video rendering or code compiling",
      "Return of full HDMI and SD card ports eliminates dongle clutter",
    ],
    cons: [
      "Premium investment price point",
    ],
    whoIsItFor: "Designers, software engineers, and media creators who need workstation power with all-day mobile battery life.",
    hook: "The Ultimate Creator Workstation",
    hashtags: ["#MacBookPro", "#DeskSetup", "#AppleSilicon", "#TechInspiration", "#AmazonAssociate"],
  },
};

export function getProductBySlug(slug: string): CatalogProduct | null {
  if (VERIFIED_PRODUCTS[slug]) {
    return VERIFIED_PRODUCTS[slug];
  }
  // Try matching by ASIN inside slug
  const match = slug.match(/([a-z0-9]{10})$/i);
  if (match) {
    const asin = match[1].toUpperCase();
    for (const prod of Object.values(VERIFIED_PRODUCTS)) {
      if (prod.asin.toUpperCase() === asin) {
        return prod;
      }
    }
  }
  return null;
}
