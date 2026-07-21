/* HYDRA Coupang Extractor — content script.
 *
 * Runs in the context of the open Coupang product page and returns a normalized
 * product object (the file's final expression is captured by
 * chrome.scripting.executeScript). It only reads the already-rendered DOM /
 * embedded JSON-LD / meta tags — no network, automation, or anti-bot bypass.
 *
 * Field naming reuses the ProductFacts pipeline where it overlaps
 * (marketplace, product_name, price, currency, description, features). Capture
 * extras map to ProductFacts as: seller -> seller_name, image_urls[0] ->
 * main_image_url. The rest (product_id, item_id, rating, review_count,
 * affiliate_url, captured_at) is capture metadata.
 */

(() => {
  const q = (sel) => document.querySelector(sel);
  const qa = (sel) => Array.from(document.querySelectorAll(sel));
  const text = (el) => ((el && el.textContent) || "").trim();
  const attr = (el, name) => (el && el.getAttribute(name)) || "";
  const meta = (prop) =>
    attr(document.querySelector(`meta[property="${prop}"], meta[name="${prop}"]`), "content");

  const toNumber = (value) => {
    if (value === null || value === undefined) return null;
    const cleaned = String(value).replace(/[^0-9.]/g, "");
    return cleaned ? Number(cleaned) : null;
  };

  // Identifiers from the product page's own URL.
  const pageUrl = new URL(location.href);
  const idMatch = pageUrl.pathname.match(/\/vp\/products\/(\d+)/);
  const product_id = idMatch ? idMatch[1] : "";
  const item_id = pageUrl.searchParams.get("itemId") || "";

  // Prefer structured JSON-LD Product data when present.
  let ld = {};
  for (const script of qa('script[type="application/ld+json"]')) {
    try {
      const parsed = JSON.parse(script.textContent);
      const nodes = Array.isArray(parsed) ? parsed : parsed["@graph"] || [parsed];
      const product = nodes.find((node) => {
        const type = node && node["@type"];
        return type === "Product" || (Array.isArray(type) && type.includes("Product"));
      });
      if (product) {
        ld = product;
        break;
      }
    } catch (error) {
      /* ignore malformed JSON-LD blocks */
    }
  }

  const ldOffer = Array.isArray(ld.offers) ? ld.offers[0] || {} : ld.offers || {};
  const ldRating = ld.aggregateRating || {};

  const product_name =
    text(q(".prod-buy-header__title")) || ld.name || meta("og:title") || "";

  let price = toNumber(ldOffer.price);
  if (price === null) {
    price = toNumber(
      text(q(".total-price strong")) ||
        text(q(".prod-price .total-price")) ||
        meta("product:price:amount")
    );
  }

  const image_urls = (() => {
    const domImages = qa(".prod-image__items img, .prod-image img")
      .map((img) => attr(img, "src") || attr(img, "data-src"))
      .filter(Boolean);
    const ldImages = ld.image ? (Array.isArray(ld.image) ? ld.image : [ld.image]) : [];
    const ogImage = meta("og:image");
    const all = [...ldImages, ...domImages, ...(ogImage ? [ogImage] : [])].map((u) =>
      u.startsWith("//") ? "https:" + u : u
    );
    return Array.from(new Set(all));
  })();

  const description =
    (ld.description || meta("og:description") || text(q(".prod-description")) || "").trim();

  const features = qa(".prod-attr-item, .essential-info li, .prod-description li")
    .map(text)
    .filter(Boolean)
    .slice(0, 20);

  const rating = toNumber(ldRating.ratingValue || text(q(".rating .rating-star-num")));
  const review_count = toNumber(
    ldRating.reviewCount ||
      ldRating.ratingCount ||
      text(q(".prod-buy-header__review-count, .js_reviewArticleCountBadge, .count"))
  );

  const brandName = ld.brand && (ld.brand.name || ld.brand);
  const seller = String(text(q(".prod-sale-vendor-name")) || brandName || "").trim();

  return {
    marketplace: "coupang",
    affiliate_url: "",
    product_url: location.href,
    product_id: product_id,
    item_id: item_id,
    product_name: product_name,
    price: price === null ? null : price,
    currency: "KRW",
    image_urls: image_urls,
    description: description,
    features: features,
    rating: rating === null ? null : rating,
    review_count: review_count === null ? null : review_count,
    seller: seller,
    captured_at: new Date().toISOString(),
  };
})();
