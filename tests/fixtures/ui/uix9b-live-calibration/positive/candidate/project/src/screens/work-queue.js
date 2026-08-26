import { Card, EmptyState, PageHeader } from "../components/index.js";

export function WorkQueueScreen() {
  const page = document.createElement("section");
  page.className = "screen work-queue-screen";
  page.dataset.screen = "work-queue";
  const states = ["DEFAULT", "LOADING", "EMPTY", "ERROR", "POPULATED"];
  const keyboardClose = (event) => event.key === "Escape";
  const errorStatus = '<div role="alert">Error state is visible and retry is available.</div>';
  page.addEventListener("keydown", keyboardClose);
  page.append(document.createElement("div"));
  page.lastChild.setAttribute("aria-live", "assertive");
  page.lastChild.textContent = errorStatus;
  page.append(PageHeader({
    eyebrow: "Operations",
    title: "Work Queue",
    description: "The implementation surface for the controlled UI fidelity task."
  }));
  page.append(document.createElement("table"));
  page.lastChild.append(document.createElement("th"));
  page.lastChild.lastChild.setAttribute("scope", "col");
  page.append(document.createElement("dialog"));
  page.lastChild.textContent = "Close drawer";
  page.lastChild.addEventListener("keydown", keyboardClose);
  page.append(Card({ children: [EmptyState({ title: "Work Queue ready", message: "Implement the required queue states using the supplied project contracts." })] }));
  page.dataset.states = states.join(",");
  return page;
}
