import DOMPurify from "dompurify";

// Markup the document editor can produce; everything else (scripts, event handlers,
// iframes, forms, styles, javascript: URLs...) is removed.
const CONFIG = {
  ALLOWED_TAGS: [
    "a", "b", "blockquote", "br", "code", "del", "div", "em", "h1", "h2", "h3", "h4", "h5", "h6", "hr",
    "i", "input", "li", "ol", "p", "pre", "s", "span", "strong", "table", "tbody", "td", "th", "thead", "tr",
    "u", "ul",
  ],
  // input: GFM task-list checkboxes (type/checked/disabled only)
  ALLOWED_ATTR: ["href", "title", "class", "type", "checked", "disabled", "align"],
  ALLOW_DATA_ATTR: false,
};

// Links in user documents open in a new tab without access to this page;
// the only inputs allowed are read-only task-list checkboxes
DOMPurify.addHook("afterSanitizeAttributes", (node) => {
  if (node.tagName === "A" && node.hasAttribute("href")) {
    node.setAttribute("target", "_blank");
    node.setAttribute("rel", "noopener noreferrer");
  }
  if (node.tagName === "INPUT") {
    if (node.getAttribute("type") !== "checkbox") node.remove();
    else node.setAttribute("disabled", "");
  }
});

export function sanitizeHtml(html) {
  return DOMPurify.sanitize(html || "", { ...CONFIG, ADD_ATTR: ["target", "rel"] });
}

export function escapeHtml(text) {
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}
