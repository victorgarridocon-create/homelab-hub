<script>
  import { tick } from "svelte";
  import { t } from "../../lib/i18n.js";
  import { renderMarkdown } from "../../lib/markdown.js";
  import { promptDialog } from "../../lib/dialog.js";

  export let content = "";
  export let onChange = () => {};

  let textarea;
  let mode = "split"; // "edit", "split", "preview"
  let localContent = content;

  // Only update when content changes from outside (document switch)
  $: if (content !== localContent) localContent = content;

  $: html = mode === "edit" ? "" : renderMarkdown(localContent);

  function update(value) {
    localContent = value;
    onChange(localContent);
  }

  /** Wrap the selection (or a placeholder) with markdown markers. */
  async function wrap(before, after = before, placeholder = "") {
    if (!textarea) return;
    const { selectionStart: start, selectionEnd: end } = textarea;
    const selected = localContent.slice(start, end) || placeholder;
    update(localContent.slice(0, start) + before + selected + after + localContent.slice(end));
    await tick();
    textarea.focus();
    textarea.setSelectionRange(start + before.length, start + before.length + selected.length);
  }

  /** Prefix every selected line (headings, lists, quotes). */
  async function prefixLines(prefix) {
    if (!textarea) return;
    const { selectionStart: start, selectionEnd: end } = textarea;
    const lineStart = localContent.lastIndexOf("\n", start - 1) + 1;
    const block = localContent.slice(lineStart, end);
    const lines = block.split("\n").map((line, i) => (typeof prefix === "function" ? prefix(i) : prefix) + line.replace(/^(#{1,6} |[-*] |\d+\. |> )/, ""));
    const replaced = lines.join("\n");
    update(localContent.slice(0, lineStart) + replaced + localContent.slice(end));
    await tick();
    textarea.focus();
    textarea.setSelectionRange(lineStart, lineStart + replaced.length);
  }

  async function insertLink() {
    const selection = textarea ? localContent.slice(textarea.selectionStart, textarea.selectionEnd) : "";
    const url = await promptDialog($t("docs.enterUrl"), { title: $t("docs.insertLink"), placeholder: "https://" });
    if (url) wrap("[", `](${url})`, selection || $t("docs.link"));
  }

  // Common shortcuts while typing
  function onKeydown(event) {
    if (!(event.ctrlKey || event.metaKey)) return;
    const key = event.key.toLowerCase();
    if (key === "b") {
      event.preventDefault();
      wrap("**", "**", $t("docs.bold"));
    } else if (key === "i") {
      event.preventDefault();
      wrap("*", "*", $t("docs.italic"));
    } else if (key === "k") {
      event.preventDefault();
      event.stopPropagation(); // don't open the global search
      insertLink();
    }
  }

  const TOOLS = [
    { label: "B", title: "docs.bold", style: "font-weight:700", run: () => wrap("**", "**", $t("docs.bold")) },
    { label: "I", title: "docs.italic", style: "font-style:italic", run: () => wrap("*", "*", $t("docs.italic")) },
    { label: "S", title: "docs.strike", style: "text-decoration:line-through", run: () => wrap("~~", "~~", "") },
    null,
    { label: "H1", title: "docs.h1", run: () => prefixLines("# ") },
    { label: "H2", title: "docs.h2", run: () => prefixLines("## ") },
    { label: "H3", title: "docs.h3", run: () => prefixLines("### ") },
    null,
    { label: "•", title: "docs.bulletList", run: () => prefixLines("- ") },
    { label: "1.", title: "docs.numberedList", run: () => prefixLines((i) => `${i + 1}. `) },
    { label: "☐", title: "docs.taskList", run: () => prefixLines("- [ ] ") },
    { label: "❝", title: "docs.quote", run: () => prefixLines("> ") },
    null,
    { label: "</>", title: "docs.code", run: () => wrap("`", "`", "code") },
    { label: "{ }", title: "docs.codeBlock", run: () => wrap("```\n", "\n```", "") },
    { label: "🔗", title: "docs.insertLink", run: insertLink },
  ];
</script>

<div class="editor-container">
  <div class="editor-bar">
    <div class="tools" role="toolbar" aria-label={$t("docs.formatting")}>
      {#each TOOLS as tool}
        {#if tool}
          <button type="button" title={$t(tool.title)} aria-label={$t(tool.title)} disabled={mode === "preview"}
            on:click={tool.run}><span style={tool.style || ""} aria-hidden="true">{tool.label}</span></button>
        {:else}
          <span class="separator" aria-hidden="true"></span>
        {/if}
      {/each}
    </div>
    <div class="modes" role="group" aria-label={$t("docs.view")}>
      <button type="button" aria-pressed={mode === "edit"} class:active={mode === "edit"} on:click={() => (mode = "edit")}>{$t("common.edit")}</button>
      <button type="button" aria-pressed={mode === "split"} class:active={mode === "split"} class="split-btn" on:click={() => (mode = "split")}>{$t("docs.split")}</button>
      <button type="button" aria-pressed={mode === "preview"} class:active={mode === "preview"} on:click={() => (mode = "preview")}>{$t("docs.preview")}</button>
    </div>
  </div>

  <div class="editor-panels mode-{mode}">
    {#if mode !== "preview"}
      <textarea
        class="editor-textarea"
        bind:this={textarea}
        value={localContent}
        on:input={(e) => update(e.target.value)}
        on:keydown={onKeydown}
        placeholder={$t("docs.writeHere")}
        aria-label={$t("docs.writeHere")}
        spellcheck="true"
      ></textarea>
    {/if}
    {#if mode !== "edit"}
      <div class="editor-preview markdown-body" aria-live="off">
        {#if html}
          {@html html}
        {:else}
          <p class="muted">{$t("docs.emptyPreview")}</p>
        {/if}
      </div>
    {/if}
  </div>
</div>

<style>
  .editor-container {
    display: flex;
    flex-direction: column;
    height: 100%;
    min-height: 0;
  }
  .editor-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 0.5rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid var(--hub-border);
  }
  .tools,
  .modes {
    display: flex;
    align-items: center;
    gap: 0.2rem;
    flex-wrap: wrap;
  }
  .tools button,
  .modes button {
    width: auto;
    margin: 0;
    padding: 0.25rem 0.55rem;
    font-size: 0.85rem;
    min-width: 2rem;
    background: transparent;
    color: var(--hub-text);
    border: 1px solid transparent;
    border-radius: 4px;
  }
  .tools button:hover:not(:disabled),
  .modes button:hover {
    background: var(--hub-surface-hover);
    border-color: var(--hub-border);
  }
  .tools button:disabled {
    opacity: 0.35;
  }
  .modes button.active {
    background: var(--pico-primary-background);
    color: var(--pico-primary-inverse);
  }
  .separator {
    width: 1px;
    height: 1.2rem;
    background: var(--hub-border);
    margin: 0 0.25rem;
  }

  .editor-panels {
    flex: 1;
    display: grid;
    grid-template-columns: 1fr;
    gap: 1rem;
    min-height: 0;
    padding-top: 0.75rem;
  }
  .editor-panels.mode-split {
    grid-template-columns: 1fr 1fr;
  }
  .editor-textarea {
    width: 100%;
    height: 100%;
    min-height: 60vh;
    margin: 0;
    resize: vertical;
    font-family: var(--pico-font-family-monospace);
    font-size: 0.9rem;
    line-height: 1.6;
  }
  .editor-preview {
    overflow-y: auto;
    min-height: 60vh;
    padding: 0.5rem 1rem;
    border: 1px solid var(--hub-border);
    border-radius: var(--pico-border-radius);
    background: var(--hub-surface);
  }
  .editor-preview :global(pre) {
    padding: 0.75rem;
    overflow-x: auto;
  }
  .editor-preview :global(blockquote) {
    border-left: 3px solid var(--hub-border);
    margin-left: 0;
    padding-left: 1rem;
    color: var(--pico-muted-color);
  }
  .editor-preview :global(table) {
    width: auto;
  }
  .editor-preview :global(li:has(> input[type="checkbox"])) {
    list-style: none;
  }

  @media (max-width: 900px) {
    /* Side by side doesn't fit: split behaves like edit + preview stacked */
    .editor-panels.mode-split {
      grid-template-columns: 1fr;
    }
    .editor-textarea,
    .editor-preview {
      min-height: 40vh;
    }
  }
</style>
