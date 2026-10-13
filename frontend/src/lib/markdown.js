import { marked } from "marked";
import { sanitizeHtml } from "./sanitize.js";

// GitHub-flavoured markdown (tables, task lists, strikethrough); single newlines become <br>
marked.setOptions({ gfm: true, breaks: true });

/**
 * Markdown → safe HTML. Documents are user content (and can arrive through Import Data),
 * so the parser output always goes through the sanitizer; marked escapes code blocks itself.
 */
export function renderMarkdown(md) {
  if (!md) return "";
  return sanitizeHtml(marked.parse(md, { async: false }));
}
