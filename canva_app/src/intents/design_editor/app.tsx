import { useFeatureSupport } from "@canva/app-hooks";
import { Button, Rows, Text, TextInput } from "@canva/app-ui-kit";
import { addElementAtCursor, addElementAtPoint } from "@canva/design";
import { useState } from "react";
import * as styles from "styles/components.css";

export const DOCS_URL = "https://www.canva.dev/docs/apps/";

const DEFAULT_PRODUCT = {
  asin: "B087F5K713",
  title: "Aesthetic Minimalist Desk Organizer & Monitor Stand",
  price: "$28.99",
  discount: "25% OFF",
  rating: "⭐ 4.8 (3,400+ reviews)",
  hook: "The Viral Desk Hack Everyone Needs",
  imageUrl: "https://m.media-amazon.com/images/I/71+8M4pS+SL._AC_SL1500_.jpg",
  tag: "smartspace07-21",
};

export const App = () => {
  const isSupported = useFeatureSupport();
  const addElement = [addElementAtPoint, addElementAtCursor].find((fn) =>
    isSupported(fn)
  );

  const [product, setProduct] = useState(DEFAULT_PRODUCT);
  const [asinInput, setAsinInput] = useState(DEFAULT_PRODUCT.asin);
  const [statusMsg, setStatusMsg] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleInsertHeadline = () => {
    if (!addElement) return;
    addElement({
      type: "text",
      children: [product.hook],
    });
    setStatusMsg("Added headline to canvas!");
  };

  const handleInsertPricePill = () => {
    if (!addElement) return;
    addElement({
      type: "text",
      children: [`${product.price} — ${product.discount}`],
    });
    setStatusMsg("Added price pill to canvas!");
  };

  const handleInsertFullLayout = () => {
    if (!addElement) return;
    addElement({
      type: "text",
      children: [
        `${product.hook.toUpperCase()}\n\n${product.title}\n\n${product.price} (${product.discount})\n${product.rating}\n\n👉 Tap link for today's Amazon deal! #AmazonAssociate`,
      ],
    });
    setStatusMsg("Inserted complete Smart Spaces 2:3 Pin layout!");
  };

  const handleFetchAiTrending = async () => {
    setIsLoading(true);
    setStatusMsg("AI Trend Hunter searching Amazon...");
    try {
      const res = await fetch("http://127.0.0.1:8000/api/ai/hunt-and-publish?publish_live=false", {
        method: "POST",
      });
      if (res.ok) {
        const data = await res.json();
        if (data.product) {
          setProduct({
            asin: data.product.asin,
            title: data.product.title,
            price: data.product.price,
            discount: "SPECIAL DEAL",
            rating: `⭐ ${data.product.rating} stars`,
            hook: data.ai_vision?.visual_hook || data.seo_copy?.title || "Viral Space-Saving Amazon Find",
            imageUrl: data.product.image_url || DEFAULT_PRODUCT.imageUrl,
            tag: "smartspace07-21",
          });
          setAsinInput(data.product.asin);
          setStatusMsg(`Found: ${data.product.title.slice(0, 35)}...`);
        }
      } else {
        setStatusMsg("Using curated Smart Spaces trending product.");
      }
    } catch {
      setStatusMsg("Connected to offline local fallback (Engine offline).");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={styles.scrollContainer} style={{ padding: "16px" }}>
      <Rows spacing="2u">
        {/* Brand Header */}
        <div style={{ borderBottom: "1px solid #e2e8f0", paddingBottom: "12px" }}>
          <Text size="large">
            <strong>Smart Spaces AI Studio</strong>
          </Text>
          <Text size="small">
            Autonomous 2:3 Pinterest Affiliate Publisher (@Smart_Spaces)
          </Text>
          <div style={{ marginTop: "4px", fontSize: "11px", color: "#059669", fontWeight: 600 }}>
            ● Tag: smartspace07-21 (Active)
          </div>
        </div>

        {/* AI Trend Hunter Action */}
        <Button
          variant="primary"
          onClick={handleFetchAiTrending}
          loading={isLoading}
        >
          ⚡ AI Hunt Trending Product
        </Button>

        {/* Manual ASIN / Product Box */}
        <div>
          <div style={{ fontSize: "12px", marginBottom: "4px", fontWeight: 600 }}>Product ASIN / URL:</div>
          <TextInput
            value={asinInput}
            onChange={(val) => setAsinInput(val)}
            placeholder="e.g. B087F5K713"
          />
        </div>

        {/* Current Active Product Card */}
        <div
          style={{
            background: "#f8fafc",
            border: "1px solid #cbd5e1",
            borderRadius: "8px",
            padding: "12px",
          }}
        >
          <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
            <img
              src={product.imageUrl}
              alt={product.title}
              style={{
                width: "56px",
                height: "56px",
                objectFit: "contain",
                borderRadius: "4px",
                background: "#fff",
              }}
            />
            <div style={{ flex: 1, minWidth: 0 }}>
              <div
                style={{
                  fontSize: "12px",
                  fontWeight: 600,
                  whiteSpace: "nowrap",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                }}
              >
                {product.title}
              </div>
              <div style={{ fontSize: "13px", color: "#0284c7", fontWeight: 700 }}>
                {product.price}{" "}
                <span style={{ fontSize: "11px", color: "#d97706" }}>
                  ({product.discount})
                </span>
              </div>
              <div style={{ fontSize: "11px", color: "#64748b" }}>
                {product.rating}
              </div>
            </div>
          </div>
        </div>

        {/* Canvas Insertion Tools */}
        <Text>
          <strong>1-Click Canvas Actions:</strong>
        </Text>

        <Button
          variant="secondary"
          onClick={handleInsertHeadline}
          disabled={!addElement}
        >
          Insert AI Headline Hook
        </Button>

        <Button
          variant="secondary"
          onClick={handleInsertPricePill}
          disabled={!addElement}
        >
          Insert Price & Deal Pill
        </Button>

        <Button
          variant="secondary"
          onClick={handleInsertFullLayout}
          disabled={!addElement}
        >
          Insert Full 2:3 Pin Layout
        </Button>

        {statusMsg && (
          <div
            style={{
              padding: "8px 12px",
              background: "#ecfdf5",
              color: "#065f46",
              borderRadius: "6px",
              fontSize: "12px",
              fontWeight: 500,
            }}
          >
            {statusMsg}
          </div>
        )}
      </Rows>
    </div>
  );
};
