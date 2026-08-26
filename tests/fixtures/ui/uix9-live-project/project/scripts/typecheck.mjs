import { readdir, readFile } from "node:fs/promises";
import { join } from "node:path";
import { spawnSync } from "node:child_process";

async function files(root) {
  const output = [];
  for (const entry of await readdir(root, { withFileTypes: true })) {
    const path = join(root, entry.name);
    if (entry.isDirectory()) output.push(...await files(path));
    else if (entry.name.endsWith(".js") || entry.name.endsWith(".mjs")) output.push(path);
  }
  return output;
}

for (const path of await files("src")) {
  const result = spawnSync(process.execPath, ["--check", path], { encoding: "utf8" });
  if (result.status !== 0) throw new Error(`${path}: ${result.stderr}`);
}

const primitives = await readFile("src/components/primitives.js", "utf8");
for (const name of ["AppShell", "Sidebar", "PageHeader", "Button", "StatusBadge", "StatCard", "DataTable", "Alert", "EmptyState", "Drawer", "Card", "FormField"]) {
  if (!primitives.includes(`function ${name}`)) throw new Error(`missing project-native component: ${name}`);
}
console.log(`TYPECHECK_PASS files=${(await files("src")).length}`);
