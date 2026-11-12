/**
 * PinForge AI — Verified Seed Catalog & Product Store
 * High-converting Smart Space Home & Organization products ready for immediate 1-click generation and bridge pages.
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
  "under-sink-sliding-organizer": {
    asin: "B093GKKQ65",
    slug: "under-sink-sliding-organizer",
    title: "2-Tier Under Sink Sliding Drawer Organizer and Storage Rack for Cabinets",
    shortTitle: "2-Tier Under Sink Sliding Drawer",
    brand: "SpaceAid",
    category: "Space Saving Kitchens",
    boardName: "Space Saving Kitchens",
    price: "$24.99",
    originalPrice: "$35.99",
    discountPercent: 31,
    rating: 4.7,
    reviewCount: "5,820+ ratings",
    imageUrl: "https://m.media-amazon.com/images/I/71Y8+gS7JTL.jpg",
    additionalImages: [],
    features: [
      "L-shaped 2-tier design leaves clearance for plumbing pipes and garbage disposals",
      "Smooth slide-out bottom drawer with built-in handles for effortless under-cabinet access",
      "100% renter-friendly damage-free freestanding installation with zero drilling required",
      "Engineered with durable ABS plastic and rust-proof stainless steel support pipes",
    ],
    verdict: "The definitive solution for chaotic under-sink cabinets, doubling vertical storage without hitting plumbing pipes.",
    pros: [
      "Smooth gliding bottom drawer prevents reaching into dark cabinet corners",
      "Zero drilling or tools needed; completely damage-free for apartment renters",
      "Elevated bottom shelf stays completely dry even during minor sink drips",
    ],
    cons: [
      "Measure your sink depth before purchase to ensure proper cabinet door closure",
    ],
    whoIsItFor: "Apartment dwellers, renters, and homeowners struggling with cluttered under-sink kitchen or bathroom cabinets.",
    hook: "Double Your Under-Sink Space in 60 Seconds",
    hashtags: ["#SmallKitchenHacks", "#UnderSinkStorage", "#ApartmentOrganization", "#RenterFriendly", "#AmazonAssociate"],
  },
  "under-bed-storage-with-wheels": {
    asin: "B0CCCR2Z9V",
    slug: "under-bed-storage-with-wheels",
    title: "Metal Under Bed Storage Containers with 360° Rotating Wheels and Clear Dust Cover",
    shortTitle: "Under Bed Rolling Storage with Wheels",
    brand: "Yecaye",
    category: "Closet & Wardrobe Organization",
    boardName: "Closet & Wardrobe Organization",
    price: "$39.99",
    originalPrice: "$49.99",
    discountPercent: 20,
    rating: 4.8,
    reviewCount: "3,640+ ratings",
    imageUrl: "https://m.media-amazon.com/images/I/71qZ7eF9KqL.jpg",
    additionalImages: [],
    features: [
      "Heavy-duty carbon steel frame supports up to 60 lbs of seasonal clothes and bulky bedding",
      "360-degree silent caster wheels roll smoothly across high-pile rugs, hardwoods, and carpets",
      "Visual transparent zipper dust cover protects textiles from pet hair and dust while keeping items visible",
      "Low-profile 6.5-inch clearance slips effortlessly under standard bed frames",
    ],
    verdict: "Turns forgotten dead space underneath your bed into a high-capacity rolling wardrobe with zero floor clutter.",
    pros: [
      "Heavy-duty metal frame will never buckle or sag like cheap fabric bins",
      "Two lockable caster wheels prevent unwanted sliding during bed movement",
      "Crystal-clear PVC window lets you see inside without unzipping",
    ],
    cons: [
      "Requires minimum 6.5 inches of clearance between floor and bed frame",
    ],
    whoIsItFor: "Studio apartment residents and compact bedroom owners needing hidden seasonal wardrobe storage.",
    hook: "Turn Dead Space Under Your Bed Into Hidden Closets",
    hashtags: ["#UnderBedStorage", "#ClosetOrganization", "#SmallApartmentLiving", "#DeclutterHome", "#AmazonAssociate"],
  },
  "magnetic-refrigerator-spice-rack": {
    asin: "B08332N66L",
    slug: "magnetic-refrigerator-spice-rack",
    title: "SpaceAid 4-Pack Heavy Duty Magnetic Spice Rack Organizer for Refrigerator",
    shortTitle: "Magnetic Fridge Spice Rack 4-Pack",
    brand: "SpaceAid",
    category: "Space Saving Kitchens",
    boardName: "Space Saving Kitchens",
    price: "$29.99",
    originalPrice: "$39.99",
    discountPercent: 25,
    rating: 4.8,
    reviewCount: "8,920+ ratings",
    imageUrl: "https://m.media-amazon.com/images/I/81xU21vGZSL.jpg",
    additionalImages: [],
    features: [
      "Ultra-strong full-back magnetic sheet holds up to 11 lbs each without slipping down fridge sides",
      "Instantly converts useless vertical refrigerator space into accessible spice and seasoning storage",
      "Matte black rust-proof alloy steel with 1.7-inch protective safety guardrails",
      "Includes 4 movable utility hooks for hanging measuring spoons, oven mitts, and dish towels",
    ],
    verdict: "The fastest way to reclaim precious kitchen countertop space without drilling a single screw.",
    pros: [
      "Insanely strong magnetic grip stays locked even when slamming refrigerator doors",
      "Zero installation time; slap it onto any metal surface and load spices immediately",
      "Frees up 2 entire cabinet shelves and leaves spices right at eye level",
    ],
    cons: [
      "Requires a magnetic metal refrigerator surface (does not adhere to non-magnetic stainless)",
    ],
    whoIsItFor: "Home cooks with tiny kitchens, zero pantry space, or crowded spice cabinets.",
    hook: "Reclaim Your Kitchen Countertops in 5 Seconds",
    hashtags: ["#KitchenHacks", "#MagneticSpiceRack", "#PantryOrganization", "#SmallKitchenIdeas", "#AmazonAssociate"],
  },
  "slim-slide-out-rolling-cart": {
    asin: "B08151T931",
    slug: "slim-slide-out-rolling-cart",
    title: "VASAGLE 4-Tier Slim Rolling Storage Cart Slide Out Gap Utility Organizer with Wheels",
    shortTitle: "VASAGLE 4-Tier Slim Rolling Cart",
    brand: "VASAGLE",
    category: "Small Apartment Hacks",
    boardName: "Small Apartment Hacks",
    price: "$32.99",
    originalPrice: "$39.99",
    discountPercent: 18,
    rating: 4.6,
    reviewCount: "14,200+ ratings",
    imageUrl: "https://m.media-amazon.com/images/I/71N1uB9y3JL.jpg",
    additionalImages: [],
    features: [
      "5.1-inch ultra-narrow footprint fits into tight crevices beside refrigerators, washers, and vanities",
      "4 durable tier baskets with safety side rails to prevent cleaning supplies or jars from falling",
      "4 heavy-duty 360-degree wheels with ergonomic handle for smooth one-hand pull out",
      "Waterproof, easy-to-wipe polypropylene construction built for humid bathrooms and laundry rooms",
    ],
    verdict: "Monetizes the dead 5-inch gap between your fridge and wall with 4 tiers of high-density storage.",
    pros: [
      "Slides completely hidden into narrow gaps you couldn't use for anything else",
      "Lightweight yet holds detergent bottles, oil dispensers, and pantry items without wobbling",
      "Smooth casters glide quietly over tile, laminate, and hardwood",
    ],
    cons: [
      "Shelves are 5.1 inches wide, so extra-wide items will need to go on the top shelf",
    ],
    whoIsItFor: "Small apartment dwellers seeking to exploit every square inch of dead gap space in kitchens and bathrooms.",
    hook: "Use That Dead 5-Inch Gap Beside Your Fridge",
    hashtags: ["#ApartmentHacks", "#SlimRollingCart", "#SmallSpaceSolutions", "#NarrowStorage", "#AmazonAssociate"],
  },
  "wall-mounted-folding-murphy-desk": {
    asin: "B0H296PMTP",
    slug: "wall-mounted-folding-murphy-desk",
    title: "Wall-Mounted Drop-Leaf Folding Table & Floating Murphy Desk for Small Spaces",
    shortTitle: "Wall-Mounted Folding Murphy Desk",
    brand: "Homary",
    category: "Studio Living Ideas",
    boardName: "Studio Living Ideas",
    price: "$69.99",
    originalPrice: "$89.99",
    discountPercent: 22,
    rating: 4.7,
    reviewCount: "2,180+ ratings",
    imageUrl: "https://m.media-amazon.com/images/I/71W7zZ2aJHL.jpg",
    additionalImages: [],
    features: [
      "Folds completely flat against the wall with a single latch release when not in use",
      "Heavy-duty cold-rolled triangular steel brackets support up to 110 lbs of distributed weight",
      "Multi-purpose surface serves as a laptop workstation, breakfast bar, sewing desk, or laundry folding table",
      "Smooth scratch-resistant rounded edge tabletop prevents accidental corner bumps",
    ],
    verdict: "A full-sized work desk when you need to be productive that completely vanishes when you need your floor back.",
    pros: [
      "Reclaims entire floor space in micro-studios and tiny bedrooms",
      "Sturdy steel bracket locks firmly in place with zero table wobble while typing",
      "Modern clean aesthetic looks like sleek wall trim when folded down",
    ],
    cons: [
      "Requires secure wall anchoring into wall studs or heavy-duty masonry anchors",
    ],
    whoIsItFor: "Studio apartment residents, remote workers in compact spaces, and tiny home minimalists.",
    hook: "Full Work Desk When Working, Floor Space When Done",
    hashtags: ["#StudioApartment", "#MurphyDesk", "#SpaceSavingFurniture", "#FoldingTable", "#AmazonAssociate"],
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
