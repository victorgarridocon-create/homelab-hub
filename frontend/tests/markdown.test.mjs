// XSS regression tests for the document renderer. Run with: npm test
import { test } from "node:test";
import assert from "node:assert/strict";
import { JSDOM } from "jsdom";

// DOMPurify needs a DOM: provide one before loading the modules under test
const { window } = new JSDOM("");
globalThis.window = window;
globalThis.document = window.document;
const { renderMarkdown } = await import("../src/lib/markdown.js");
const { sanitizeHtml } = await import("../src/lib/sanitize.js");

/** Parse the output and report anything that could run script. */
function dangerous(html) {
  const doc = new JSDOM(`<body>${html}</body>`).window.document;
  const problems = [];
  for (const el of doc.body.querySelectorAll("*")) {
    if (["SCRIPT", "IFRAME", "OBJECT", "EMBED", "STYLE", "FORM", "SVG", "MATH"].includes(el.tagName.toUpperCase())) {
      problems.push(`<${el.tagName.toLowerCase()}>`);
    }
    for (const attr of el.attributes) {
      if (attr.name.startsWith("on")) problems.push(`${attr.name}=`);
      if (["href", "src", "xlink:href", "action"].includes(attr.name) && /^\s*(javascript|data|vbscript):/i.test(attr.value)) {
        problems.push(`${attr.name}=${attr.value}`);
      }
    }
  }
  return problems;
}

const PAYLOADS = [
  "<script>alert(1)</script>",
  "<img src=x onerror=alert(1)>",
  "<svg onload=alert(1)>",
  "<iframe src=\"javascript:alert(1)\"></iframe>",
  "[click](javascript:alert(1))",
  "[click](JaVaScRiPt:alert(1))",
  "[click](data:text/html;base64,PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg==)",
  "[x\" onmouseover=\"alert(1)](https://example.com)",
  "[x](https://example.com\" onclick=\"alert(1))",
  "# <img src=x onerror=alert(1)>",
  "**<b onclick=alert(1)>bold</b>**",
  "> <details open ontoggle=alert(1)>",
  "<a href=\"javascript:alert(1)\">x</a>",
  "<math><mtext><table><mglyph><style><img src=x onerror=alert(1)>",
  "<form action=\"https://evil.example\"><input name=p></form>",
  "```\n<script>alert(1)</script>\n```",
];

for (const payload of PAYLOADS) {
  test(`neutralises ${payload.slice(0, 50)}`, () => {
    assert.deepEqual(dangerous(renderMarkdown(payload)), []);
  });
}

test("sanitizeHtml neutralises pasted HTML", () => {
  for (const payload of PAYLOADS) assert.deepEqual(dangerous(sanitizeHtml(payload)), []);
});

test("code blocks show markup literally", () => {
  const html = renderMarkdown("```\n<script>alert(1)</script>\n```");
  assert.match(html, /&lt;script&gt;alert\(1\)&lt;\/script&gt;/);
});

test("regular markdown still renders", () => {
  const html = renderMarkdown("# Title\n\n**bold** *it* `code`\n\n- item\n\n[site](https://example.com)");
  assert.match(html, /<h1>Title<\/h1>/);
  assert.match(html, /<strong>bold<\/strong>/);
  assert.match(html, /<em>it<\/em>/);
  assert.match(html, /<code>code<\/code>/);
  assert.match(html, /<li>item<\/li>/);
  assert.match(html, /<a href="https:\/\/example.com" target="_blank" rel="noopener noreferrer">site<\/a>/);
});
