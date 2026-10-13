import "@picocss/pico/css/pico.min.css";
import "./app.css";
import "./lib/theme.js"; // applies the saved theme before the first render
import App from "./App.svelte";

const app = new App({
  target: document.getElementById("app"),
});

export default app;
