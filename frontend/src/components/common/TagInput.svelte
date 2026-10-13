<script>
  import TagList from "./TagList.svelte";
  import { t } from "../../lib/i18n.js";

  export let value = "";
</script>

<label>
  {$t("fields.tags")}
  <input type="text" bind:value placeholder={$t("tags.placeholder")} />
  <small class="preview"><TagList tags={value} /></small>
</label>

<style>
  .preview {
    display: block;
    min-height: 0.5rem;
    margin-top: -0.5rem;
  }
</style>
