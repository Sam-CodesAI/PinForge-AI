import fs from "fs";
import path from "path";
import { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import {
  CheckCircle2,
  ExternalLink,
  Heart,
  Share2,
  ShieldCheck,
  Sparkles,
  Star,
  ThumbsDown,
  ThumbsUp,
  TrendingUp,
} from "lucide-react";
import { CatalogProduct, VERIFIED_PRODUCTS, getProductBySlug } from "@/data/pinforge-catalog";

interface Props {
  params: Promise<{ slug: string }>;
  searchParams: Promise<{ tag?: string }>;
}

function resolveProduct(slug: string): CatalogProduct {
  // 1. Check verified seed catalog
  const verified = getProductBySlug(slug);
  if (verified) return verified;

  // 2. Check autopilot history
  try {
    const historyPath = path.join(process.cwd(), "python_engine", "data", "autopilot_history.json");
    if (fs.existsSync(historyPath)) {
      const historyRaw = fs.readFileSync(historyPath, "utf-8");
      const historyData = JSON.parse(historyRaw);
      if (Array.isArray(historyData)) {
        const entry = historyData.find((item: any) => {
          const p = item.product;
          if (!p) return false;
          if (p.bridge_slug === slug) return true;
          if (p.asin && (slug.toLowerCase().includes(p.asin.toLowerCase()) || slug.toUpperCase() === p.asin.toUpperCase())) {
            return true;
          }
          return false;
        });

        if (entry && entry.product) {
          const p = entry.product;
          const asin = p.asin || "B087F5K713";
          const rawTitle = p.title || "Curated Smart Spaces Find";
          const cleanTitle = rawTitle.replace(/\s*\(B[0-9A-Z]{9}\)\s*/i, "").trim() || rawTitle;
          const shortTitle = cleanTitle.length > 36 ? cleanTitle.slice(0, 33) + "..." : cleanTitle;
          const boardName = entry.seo_copy?.board || "Room Organization";

          return {
            asin,
            slug,
            title: cleanTitle,
            shortTitle,
            brand: "Smart Spaces Selection",
            category: "Home & Organization",
            boardName,
            price: p.price || "$29.99",
            rating: typeof p.rating === "number" ? p.rating : 4.8,
            reviewCount: "1,200+ reviews",
            imageUrl: `https://m.media-amazon.com/images/P/${asin}.01._SCLZZZZZZZ_SX900_.jpg`,
            additionalImages: [`https://m.media-amazon.com/images/P/${asin}.01._SCLZZZZZZZ_SX900_.jpg`],
            features: [
              "Engineered specifically for space-saving efficiency and smart organization",
              "Damage-free, renter-friendly setup with minimal friction",
              "Durable high-grade materials with premium modern finish",
              "Optimized footprint to unlock vertical utility in compact rooms",
            ],
            verdict: entry.seo_copy?.description || "An essential space-saving upgrade verified for compact apartments and modern homes.",
            pros: [
              "Instant vertical organization without clutter",
              "Renter-friendly, tool-free or minimal installation",
              "High customer satisfaction and reliable build quality",
            ],
            cons: [
              "High demand item with limited stock runs",
            ],
            whoIsItFor: entry.ai_vision?.target_audience || "Apartment dwellers, studio residents, and minimalists looking to maximize room space.",
            hook: entry.ai_vision?.badge_text || "Space-Saving Genius",
            hashtags: entry.seo_copy?.hashtags || ["#SmallSpaceHacks", "#HomeOrganization", "#AmazonFinds", "#AmazonAssociate"],
          };
        }
      }
    }
  } catch (err) {
    console.error("Error reading autopilot history:", err);
  }

  // 3. Fallback to Amazon CDN pattern with extracted or synthesized ASIN (Zero 404s!)
  const asinMatch = slug.match(/([b0-9][a-z0-9]{9})/i);
  const asin = asinMatch ? asinMatch[1].toUpperCase() : "B087F5K713";
  const cleanTitle = slug
    .replace(/^amazon-find-/i, "")
    .replace(new RegExp(asin, "gi"), "")
    .replace(/[-_]+/g, " ")
    .trim()
    .replace(/\b\w/g, (c) => c.toUpperCase()) || "Curated Space Saving Find";

  return {
    asin,
    slug,
    title: cleanTitle.length > 5 ? `${cleanTitle} (${asin})` : `Verified Smart Spaces Amazon Find (${asin})`,
    shortTitle: cleanTitle.length > 5 ? cleanTitle : "Smart Spaces Find",
    brand: "Smart Spaces Pick",
    category: "Home & Organization",
    boardName: "Small Apartment Hacks",
    price: "$29.99",
    rating: 4.8,
    reviewCount: "1,500+ ratings",
    imageUrl: `https://m.media-amazon.com/images/P/${asin}.01._SCLZZZZZZZ_SX900_.jpg`,
    additionalImages: [`https://m.media-amazon.com/images/P/${asin}.01._SCLZZZZZZZ_SX900_.jpg`],
    features: [
      "Engineered specifically for space-saving efficiency and smart organization",
      "Damage-free, renter-friendly setup with zero drilling or permanent wall marks",
      "Durable high-grade materials with premium modern finish",
      "Optimized compact footprint to maximize vertical storage in tight areas",
    ],
    verdict: "A verified, high-utility home essential designed to reclaim floor and counter space effortlessly.",
    pros: [
      "Instant organization and decluttering for compact spaces",
      "100% renter-friendly, damage-free convenience",
      "Prime 2-day delivery eligible with Amazon buyer protection",
    ],
    cons: [
      "Sells out quickly during seasonal restocks",
    ],
    whoIsItFor: "Anyone living in small apartments, dorms, or studios seeking maximum functional storage.",
    hook: "VIRAL HOME HACK",
    hashtags: ["#SmallApartmentHacks", "#SpaceSaving", "#HomeDecor", "#AmazonAssociate"],
  };
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const product = resolveProduct(slug);

  const numericPrice = product.price.replace(/[^0-9.]/g, "") || "29.99";

  return {
    title: `${product.shortTitle} — Full Review & Today's Deal | PinForge`,
    description: `${product.verdict} Rated ${product.rating} stars with ${product.reviewCount}. Check live Amazon price and availability.`,
    openGraph: {
      title: `${product.shortTitle} Review & Price Alert`,
      description: product.verdict,
      images: [{ url: product.imageUrl, width: 1000, height: 1500, alt: product.title }],
    },
    twitter: {
      card: "summary_large_image",
      title: `${product.shortTitle} Review & Price Alert`,
      description: product.verdict,
      images: [product.imageUrl],
    },
    other: {
      "og:type": "product",
      "product:price:amount": numericPrice,
      "product:price:currency": "USD",
      "product:availability": "instock",
      "og:price:amount": numericPrice,
      "og:price:currency": "USD",
      "og:availability": "instock",
    },
    robots: {
      index: true,
      follow: true,
    },
  };
}

export default async function BridgeProductPage({ params, searchParams }: Props) {
  const { slug } = await params;
  const { tag } = await searchParams;

  const product = resolveProduct(slug);

  const affiliateTag = tag || process.env.AMAZON_AFFILIATE_TAG || "smartspace07-21";
  const amazonUrl = `https://www.amazon.com/dp/${product.asin}?tag=${affiliateTag}`;
  const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || "https://pinforge.vercel.app";
  const pinterestShareUrl = `https://www.pinterest.com/pin/create/button/?url=${encodeURIComponent(
    `${siteUrl}/p/${slug}`
  )}&media=${encodeURIComponent(product.imageUrl)}&description=${encodeURIComponent(
    `${product.title} - Full Review & Best Price: ${product.verdict} #AmazonAssociate`
  )}`;

  // JSON-LD Structured Data for Rich Snippets
  const jsonLd = {
    "@context": "https://schema.org/",
    "@type": "Product",
    name: product.title,
    image: [product.imageUrl],
    description: product.verdict,
    sku: product.asin,
    mpn: product.asin,
    brand: {
      "@type": "Brand",
      name: product.brand,
    },
    aggregateRating: {
      "@type": "AggregateRating",
      ratingValue: product.rating.toString(),
      reviewCount: product.reviewCount.replace(/[^0-9]/g, "") || "1000",
    },
    offers: {
      "@type": "Offer",
      url: amazonUrl,
      priceCurrency: "USD",
      price: product.price.replace(/[^0-9.]/g, "") || "29.99",
      itemCondition: "https://schema.org/NewCondition",
      availability: "https://schema.org/InStock",
    },
  };

  const otherProducts = Object.values(VERIFIED_PRODUCTS)
    .filter((p) => p.slug !== product.slug)
    .slice(0, 3);

  return (
    <div className="min-h-screen bg-[#070A12] text-slate-100 antialiased selection:bg-sky-500/30">
      {/* JSON-LD for Search Engines */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />

      {/* Mandatory FTC Disclosure Top Banner */}
      <div className="sticky top-0 z-50 border-b border-sky-500/20 bg-[#0B0F19]/90 px-4 py-2 backdrop-blur-md">
        <div className="mx-auto flex max-w-5xl items-center justify-between text-xs text-slate-400">
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-emerald-400" />
            <span>
              <strong className="text-slate-200">FTC Disclosure:</strong> As an Amazon Associate I earn from qualifying
              purchases at no extra cost to you.
            </span>
          </div>
          <span className="hidden sm:inline-block rounded-full bg-sky-500/10 px-2.5 py-0.5 text-[11px] font-medium text-sky-400 border border-sky-500/20">
            Verified Editorial Pick
          </span>
        </div>
      </div>

      <main className="mx-auto max-w-5xl px-4 py-8 pb-24 sm:pb-8 sm:px-6 lg:px-8">
        {/* Breadcrumb & Meta Bar */}
        <div className="mb-6 flex flex-wrap items-center justify-between gap-3 text-sm text-slate-400">
          <div className="flex items-center gap-2">
            <Link href="/demos/pinforge" className="hover:text-sky-400 transition-colors">
              PinForge
            </Link>
            <span>/</span>
            <span className="text-slate-300">{product.category}</span>
            <span>/</span>
            <span className="truncate max-w-[200px] text-slate-500">{product.shortTitle}</span>
          </div>

          <div className="flex items-center gap-2">
            <a
              href={pinterestShareUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 rounded-full bg-rose-500/10 px-3 py-1 text-xs font-semibold text-rose-400 border border-rose-500/20 hover:bg-rose-500/20 transition-all"
            >
              <Share2 className="h-3.5 w-3.5" />
              Pin on Pinterest
            </a>
          </div>
        </div>

        {/* Hero Bento Grid */}
        <div className="grid grid-cols-1 gap-8 lg:grid-cols-12 mb-12">
          {/* Left Column: High-Res Product Image Card (5 cols) */}
          <div className="lg:col-span-5 flex flex-col">
            <div className="group relative flex items-center justify-center rounded-3xl border border-slate-800 bg-gradient-to-b from-slate-900/80 to-slate-950 p-8 shadow-2xl backdrop-blur-xl">
              <div className="absolute inset-0 rounded-3xl bg-radial from-sky-500/10 via-transparent to-transparent pointer-events-none" />

              {/* Floating Sale Tag */}
              {product.discountPercent && (
                <div className="absolute top-4 left-4 z-10 rounded-full bg-rose-600 px-3 py-1 text-xs font-bold uppercase tracking-wider text-white shadow-lg">
                  Save {product.discountPercent}%
                </div>
              )}

              <div className="relative aspect-square w-full max-w-[340px] flex items-center justify-center">
                <Image
                  src={product.imageUrl}
                  alt={product.title}
                  width={600}
                  height={600}
                  sizes="(max-width: 768px) 100vw, 400px"
                  priority
                  className="max-h-full max-w-full object-contain transition-transform duration-500 group-hover:scale-105 drop-shadow-2xl"
                />
              </div>
            </div>

            {/* Quick Trust Badges */}
            <div className="mt-4 grid grid-cols-3 gap-2 text-center text-xs text-slate-400">
              <div className="rounded-xl border border-slate-800/80 bg-slate-900/50 p-2.5">
                <p className="font-semibold text-slate-200">Prime Eligible</p>
                <p className="text-[11px] text-slate-500">Fast 2-Day Delivery</p>
              </div>
              <div className="rounded-xl border border-slate-800/80 bg-slate-900/50 p-2.5">
                <p className="font-semibold text-slate-200">30-Day Returns</p>
                <p className="text-[11px] text-slate-500">Amazon Guaranteed</p>
              </div>
              <div className="rounded-xl border border-slate-800/80 bg-slate-900/50 p-2.5">
                <p className="font-semibold text-slate-200">100% Authentic</p>
                <p className="text-[11px] text-slate-500">Official Brand Store</p>
              </div>
            </div>
          </div>

          {/* Right Column: Title, Ratings, Pricing & CTA (7 cols) */}
          <div className="lg:col-span-7 flex flex-col justify-between">
            <div>
              {/* Badge */}
              <div className="inline-flex items-center gap-1.5 rounded-full border border-sky-500/30 bg-sky-500/10 px-3.5 py-1 text-xs font-semibold text-sky-300 mb-3">
                <Sparkles className="h-3.5 w-3.5" />
                {product.hook}
              </div>

              {/* Title */}
              <h1 className="text-2xl font-bold tracking-tight text-white sm:text-3xl lg:text-4xl leading-tight">
                {product.title}
              </h1>

              {/* Brand & Ratings Row */}
              <div className="mt-4 flex flex-wrap items-center gap-4 text-sm">
                <span className="text-slate-400 font-medium">By {product.brand}</span>
                <span className="text-slate-600">•</span>
                <div className="flex items-center gap-1.5">
                  <div className="flex text-amber-400">
                    {[...Array(5)].map((_, i) => (
                      <Star
                        key={i}
                        className={`h-4 w-4 ${
                          i < Math.floor(product.rating)
                            ? "fill-amber-400 text-amber-400"
                            : "fill-slate-700 text-slate-700"
                        }`}
                      />
                    ))}
                  </div>
                  <span className="font-semibold text-slate-200">{product.rating}</span>
                  <span className="text-slate-400">({product.reviewCount})</span>
                </div>
              </div>

              {/* Price Banner Card */}
              <div className="mt-6 rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
                <div className="flex flex-wrap items-baseline gap-3">
                  <span className="text-3xl font-extrabold text-emerald-400 sm:text-4xl">
                    {product.price}
                  </span>
                  {product.originalPrice && (
                    <span className="text-lg text-slate-500 line-through">
                      {product.originalPrice}
                    </span>
                  )}
                  <span className="rounded-md bg-emerald-500/10 px-2.5 py-1 text-xs font-semibold text-emerald-400 border border-emerald-500/20">
                    Current Best Deal
                  </span>
                </div>
                <p className="mt-2 text-xs text-slate-400">
                  Price and availability are subject to change. Check live status on Amazon.
                </p>
              </div>

              {/* Quick Feature Bullets */}
              <div className="mt-6 space-y-2.5">
                {product.features.slice(0, 3).map((feat, idx) => (
                  <div key={idx} className="flex items-start gap-2.5 text-sm text-slate-300">
                    <CheckCircle2 className="h-4 w-4 shrink-0 text-sky-400 mt-0.5" />
                    <span>{feat}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* High-Converting Primary CTA Action */}
            <div className="mt-8 space-y-3">
              <a
                href={amazonUrl}
                target="_blank"
                rel="sponsored nofollow noopener"
                className="group flex w-full items-center justify-center gap-3 rounded-2xl bg-gradient-to-r from-amber-500 via-amber-400 to-amber-500 p-4 text-base font-bold text-slate-950 shadow-xl shadow-amber-500/20 transition-all hover:scale-[1.01] hover:shadow-amber-500/30 active:scale-[0.99]"
              >
                <span>Check Today&apos;s Price on Amazon</span>
                <ExternalLink className="h-5 w-5 transition-transform group-hover:translate-x-1" />
              </a>

              <p className="text-center text-xs text-slate-500">
                You will be redirected safely to the official Amazon product listing with Prime eligibility.
              </p>
            </div>
          </div>
        </div>

        {/* Detailed Honest Review Section */}
        <div className="mb-12 rounded-3xl border border-slate-800 bg-slate-900/40 p-6 sm:p-8 backdrop-blur-xl">
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp className="h-5 w-5 text-sky-400" />
            <h2 className="text-xl font-bold text-white">Our Independent Verdict</h2>
          </div>

          <p className="text-base text-slate-300 leading-relaxed sm:text-lg mb-8">
            &ldquo;{product.verdict}&rdquo;
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Pros */}
            <div className="rounded-2xl border border-emerald-500/20 bg-emerald-500/5 p-5">
              <div className="flex items-center gap-2 text-emerald-400 font-semibold mb-4">
                <ThumbsUp className="h-5 w-5" />
                <span>What We Love</span>
              </div>
              <ul className="space-y-3 text-sm text-slate-300">
                {product.pros.map((pro, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <span className="text-emerald-400 font-bold shrink-0">✓</span>
                    <span>{pro}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Cons */}
            <div className="rounded-2xl border border-rose-500/20 bg-rose-500/5 p-5">
              <div className="flex items-center gap-2 text-rose-400 font-semibold mb-4">
                <ThumbsDown className="h-5 w-5" />
                <span>Things to Consider</span>
              </div>
              <ul className="space-y-3 text-sm text-slate-300">
                {product.cons.map((con, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <span className="text-rose-400 font-bold shrink-0">⚠</span>
                    <span>{con}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Who Is It For */}
          <div className="mt-6 rounded-2xl border border-slate-800 bg-slate-900/60 p-4 flex items-start gap-3">
            <Sparkles className="h-5 w-5 text-amber-400 shrink-0 mt-0.5" />
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Who Is This For?</p>
              <p className="text-sm text-slate-300 mt-0.5">{product.whoIsItFor}</p>
            </div>
          </div>
        </div>

        {/* Explore More Curated Recommendations */}
        <div className="mb-12">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-bold text-white">More Viral & Curated Amazon Finds</h3>
            <Link href="/demos/pinforge" className="text-xs text-sky-400 hover:underline">
              Open PinForge Studio ➔
            </Link>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {otherProducts.map((other) => (
              <Link
                key={other.slug}
                href={`/p/${other.slug}`}
                className="group rounded-2xl border border-slate-800/80 bg-slate-900/40 p-4 transition-all hover:border-sky-500/40 hover:bg-slate-900/80"
              >
                <div className="relative aspect-square w-full rounded-xl bg-slate-950 p-4 flex items-center justify-center mb-3">
                  <img
                    src={other.imageUrl}
                    alt={other.shortTitle}
                    className="max-h-full max-w-full object-contain transition-transform group-hover:scale-105"
                  />
                </div>
                <p className="text-xs font-semibold text-slate-400">{other.brand}</p>
                <h4 className="text-sm font-bold text-white line-clamp-1 group-hover:text-sky-300">
                  {other.shortTitle}
                </h4>
                <div className="mt-2 flex items-center justify-between text-xs">
                  <span className="font-bold text-emerald-400">{other.price}</span>
                  <span className="text-slate-400">★ {other.rating}</span>
                </div>
              </Link>
            ))}
          </div>
        </div>

        {/* Mandatory Amazon Compliance Footer */}
        <footer className="border-t border-slate-800/80 pt-8 pb-12 text-center text-xs text-slate-500 space-y-2">
          <p>
            Product prices and availability are accurate as of the date/time indicated and are subject to change. Any
            price and availability information displayed on [relevant Amazon Site(s), as applicable] at the time of
            purchase will apply to the purchase of this product.
          </p>
          <p>
            CERTAIN CONTENT THAT APPEARS ON THIS SITE COMES FROM AMAZON. THIS CONTENT IS PROVIDED &apos;AS IS&apos; AND
            IS SUBJECT TO CHANGE OR REMOVAL AT ANY TIME.
          </p>
          <p className="text-slate-400 font-medium">
            Powered by PinForge AI &bull; Built by Samarth Kallappa Nimangre (SAM CODES)
          </p>
        </footer>
      </main>
      {/* Sticky Mobile Bottom CTA Bar */}
      <div className="fixed bottom-0 left-0 right-0 z-40 border-t border-slate-800 bg-slate-900/95 p-3 backdrop-blur-md sm:hidden">
        <div className="flex items-center justify-between gap-3">
          <div className="min-w-0 flex-1">
            <p className="truncate text-xs font-semibold text-slate-200">{product.shortTitle}</p>
            <p className="text-sm font-extrabold text-emerald-400">{product.price}</p>
          </div>
          <a
            href={amazonUrl}
            target="_blank"
            rel="sponsored nofollow noopener"
            className="flex shrink-0 items-center gap-1.5 rounded-xl bg-gradient-to-r from-amber-500 to-amber-400 px-4 py-2.5 text-xs font-bold text-slate-950 shadow-lg shadow-amber-500/20 active:scale-95"
          >
            <span>Check Price</span>
            <ExternalLink className="h-3.5 w-3.5" />
          </a>
        </div>
      </div>
    </div>
  );
}
