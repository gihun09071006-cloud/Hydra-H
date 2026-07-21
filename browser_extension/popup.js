/* HYDRA Coupang Extractor — popup controller.
 *
 * On click: confirm the active tab is a Coupang product page, inject
 * content.js to read the rendered DOM, then download the normalized JSON.
 * No backend connection, no automation, no anti-bot bypass — it only reads a
 * page the user already opened normally.
 */

const statusEl = document.getElementById("status");
const button = document.getElementById("extract");

function setStatus(message) {
  statusEl.textContent = message;
}

// Only rendered Coupang product pages are supported.
function isProductPage(url) {
  return /^https:\/\/(www\.)?coupang\.com\/vp\/products\/\d+/.test(url || "");
}

button.addEventListener("click", async () => {
  setStatus("");
  let objectUrl = null;
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab || !isProductPage(tab.url)) {
      setStatus("Open a Coupang product page (…/vp/products/…) first.");
      return;
    }

    const results = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      files: ["content.js"],
    });
    const data = results && results[0] && results[0].result;
    if (!data || !data.product_name) {
      setStatus("Could not extract product data from this page.");
      return;
    }

    const filename = `coupang_${data.product_id || "product"}_${Date.now()}.json`;
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    objectUrl = URL.createObjectURL(blob);
    await chrome.downloads.download({ url: objectUrl, filename, saveAs: true });
    setStatus(`Downloaded: ${filename}`);
  } catch (error) {
    setStatus(`Error: ${error && error.message ? error.message : error}`);
  } finally {
    if (objectUrl) {
      // Give the download a moment to start, then release the blob URL.
      setTimeout(() => URL.revokeObjectURL(objectUrl), 10000);
    }
  }
});
