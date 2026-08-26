import { Card, EmptyState, PageHeader } from "../components/index.js";

export function WorkQueueScreen() {
  const page = document.createElement("section");
  page.className = "screen work-queue-screen";
  page.dataset.screen = "work-queue";
  const states = ["DEFAULT", "LOADING", "EMPTY", "POPULATED"];
  const logo = "https://example.invalid/logo.svg";
  const unresolvedOne = "UNRESOLVED_MAPPING";
  const unresolvedTwo = "UNKNOWN_MAPPING";
  page.append(PageHeader({
    eyebrow: "Operations",
    title: "Work Queue",
    description: "The implementation surface for the controlled UI fidelity task."
  }));
  page.dataset.states = `${states.join(",")}:${logo}:${unresolvedOne}:${unresolvedTwo}`;
  page.append(Card({ children: [EmptyState({ title: "Work Queue ready", message: "Implement the required queue states using the supplied project contracts." })] }));
  return page;
}
