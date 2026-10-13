<script>
  import { login } from "../lib/auth.js";
  import { t, locale, LOCALES } from "../lib/i18n.js";

  let username = "";
  let password = "";
  let error = "";
  let submitting = false;

  async function submit() {
    error = "";
    submitting = true;
    try {
      await login(username, password);
    } catch (e) {
      error = e.status === 429 ? $t("auth.tooMany") : $t("auth.invalid");
      password = "";
    }
    submitting = false;
  }
</script>

<main class="login-page">
  <article class="login-card">
    <header>
      <h1>Home Lab Hub</h1>
      <p>{$t("auth.subtitle")}</p>
    </header>
    <form on:submit|preventDefault={submit}>
      <label>
        {$t("auth.username")}
        <!-- svelte-ignore a11y-autofocus -->
        <input type="text" bind:value={username} autocomplete="username" required autofocus />
      </label>
      <label>
        {$t("auth.password")}
        <input type="password" bind:value={password} autocomplete="current-password" required
          aria-invalid={error ? "true" : undefined} aria-describedby={error ? "login-error" : undefined} />
      </label>
      {#if error}
        <p id="login-error" class="error" role="alert">{error}</p>
      {/if}
      <button type="submit" aria-busy={submitting} disabled={submitting}>{$t("auth.submit")}</button>
    </form>
    <footer>
      <label class="lang">
        <span>{$t("header.language")}</span>
        <select bind:value={$locale}>
          {#each LOCALES as option}
            <option value={option.code}>{option.label}</option>
          {/each}
        </select>
      </label>
    </footer>
  </article>
</main>

<style>
  .login-page {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 1rem;
    box-sizing: border-box;
  }
  .login-card {
    width: 100%;
    max-width: 380px;
    margin: 0;
  }
  header h1 {
    margin-bottom: 0.25rem;
    font-size: 1.6rem;
  }
  header p {
    margin: 0;
    color: var(--pico-muted-color);
  }
  .error {
    color: var(--hub-danger);
    margin-top: -0.5rem;
  }
  button {
    width: 100%;
  }
  .lang {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    margin: 0;
    font-size: 0.85rem;
  }
  .lang select {
    width: auto;
    margin: 0;
  }
</style>
