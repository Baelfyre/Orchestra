import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const fixtureRoot = new URL("..", import.meta.url);
const read = (path) => readFile(new URL(path, fixtureRoot), "utf8");

test("all required project-native components are present", async () => {
  const source = await read("src/components/primitives.js");
  for (const name of ["AppShell", "Sidebar", "PageHeader", "Button", "StatusBadge", "StatCard", "DataTable", "Alert", "EmptyState", "Drawer", "Card", "FormField"]) {
    assert.match(source, new RegExp(`function ${name}`));
  }
});

test("tokens, responsive boundaries, and accessibility safeguards are present", async () => {
  const tokens = await read("src/styles/tokens.css");
  const styles = await read("src/styles/app.css");
  assert.match(tokens, /--color-action-primary/);
  assert.match(tokens, /--breakpoint-tablet/);
  assert.match(styles, /@media \(min-width: 768px\)/);
  assert.match(styles, /@media \(min-width: 1024px\)/);
  assert.match(styles, /prefers-reduced-motion/);
  assert.match(styles, /forced-colors/);
  assert.match(styles, /:focus-visible/);
});

test("reference asset remains project-native", async () => {
  const source = await read("src/components/primitives.js");
  assert.match(source, /\.\/src\/assets\/operations-mark\.svg/);
  assert.match(await read("src/assets/operations-mark.svg"), /uix9b|Operations|2457d6/);
});
