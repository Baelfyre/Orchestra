import { mountApp } from "./app.js";

const root = document.querySelector("#app");
if (!root) throw new Error("Missing #app root");
mountApp(root);
