function createElement(tag, attributes = {}, children = []) {
  const element = document.createElement(tag);
  for (const [name, value] of Object.entries(attributes)) {
    if (value === undefined || value === null) continue;
    if (name === "className") element.className = value;
    else if (name === "textContent") element.textContent = value;
    else element.setAttribute(name, String(value));
  }
  for (const child of children) {
    if (child) element.append(child);
  }
  return element;
}

export function AppShell({ sidebar, content }) {
  return createElement("div", { className: "app-shell" }, [sidebar, createElement("main", { className: "app-main", id: "main-content", tabindex: "-1" }, [content])]);
}

export function Sidebar({ active = "Work Queue" } = {}) {
  const navigation = createElement("nav", { className: "sidebar-nav", "aria-label": "Primary navigation" });
  for (const label of ["Work Queue", "Reports", "Settings"]) {
    const link = createElement("a", { href: `#${label.toLowerCase().replaceAll(" ", "-")}`, className: label === active ? "nav-link is-active" : "nav-link" }, [label]);
    navigation.append(link);
  }
  return createElement("aside", { className: "sidebar" }, [createElement("a", { className: "brand", href: "#work-queue", "aria-label": "Operations Workspace home" }, [createElement("img", { src: "./src/assets/operations-mark.svg", alt: "" }), createElement("span", {textContent: "Operations"})]), navigation]);
}

export function PageHeader({ eyebrow, title, description, actions = [] }) {
  const heading = createElement("div", { className: "page-header-copy" }, [
    eyebrow ? createElement("p", { className: "eyebrow", textContent: eyebrow }) : null,
    createElement("h1", { textContent: title }),
    description ? createElement("p", { className: "page-description", textContent: description }) : null
  ]);
  return createElement("header", { className: "page-header" }, [heading, createElement("div", { className: "page-header-actions" }, actions)]);
}

export function Button({ label, variant = "primary", type = "button", disabled = false, ariaLabel }) {
  const button = createElement("button", { type, className: `button button-${variant}`, "aria-label": ariaLabel ?? label }, [label]);
  button.disabled = disabled;
  return button;
}

export function StatusBadge({ label, tone = "neutral" }) {
  return createElement("span", { className: `status-badge status-${tone}` }, [label]);
}

export function StatCard({ label, value, detail = "" }) {
  return createElement("article", { className: "stat-card" }, [createElement("p", { className: "stat-label", textContent: label }), createElement("p", { className: "stat-value", textContent: value }), detail ? createElement("p", { className: "stat-detail", textContent: detail }) : null]);
}

export function DataTable({ caption, headers = [], rows = [] }) {
  const table = createElement("table", { className: "data-table" });
  table.append(createElement("caption", { textContent: caption }));
  const head = createElement("thead");
  head.append(createElement("tr", {}, headers.map((header) => createElement("th", { scope: "col", textContent: header }))));
  const body = createElement("tbody");
  for (const row of rows) body.append(createElement("tr", {}, row.map((cell) => createElement("td", { textContent: cell }))));
  table.append(head, body);
  return table;
}

export function Alert({ message, tone = "info" }) {
  return createElement("div", { className: `alert alert-${tone}`, role: tone === "error" ? "alert" : "status" }, [message]);
}

export function EmptyState({ title, message, action }) {
  return createElement("div", { className: "empty-state" }, [createElement("h2", { textContent: title }), createElement("p", { textContent: message }), action ?? null]);
}

export function Drawer({ title, content, open = false, onClose }) {
  const dialog = createElement("dialog", { className: "drawer", "aria-labelledby": "drawer-title" }, [createElement("div", { className: "drawer-header" }, [createElement("h2", { id: "drawer-title", textContent: title }), Button({ label: "Close", variant: "secondary" })]), content]);
  if (open) dialog.setAttribute("open", "");
  if (onClose) dialog.querySelector("button").addEventListener("click", onClose);
  return dialog;
}

export function Card({ children = [], title }) {
  return createElement("section", { className: "card" }, [title ? createElement("h2", { textContent: title }) : null, ...children]);
}

export function FormField({ id, label, type = "text", value = "", error = "" }) {
  const input = createElement("input", { id, name: id, type, value, "aria-invalid": error ? "true" : "false", "aria-describedby": error ? `${id}-error` : undefined });
  return createElement("div", { className: "form-field" }, [createElement("label", { for: id, textContent: label }), input, error ? createElement("p", { id: `${id}-error`, className: "field-error", textContent: error }) : null]);
}
