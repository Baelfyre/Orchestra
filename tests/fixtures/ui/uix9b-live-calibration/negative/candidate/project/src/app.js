import { AppShell, Sidebar } from "./components/index.js";
import { WorkQueueScreen } from "./screens/work-queue.js";

export function mountApp(root) {
  root.replaceChildren(AppShell({ sidebar: Sidebar(), content: WorkQueueScreen() }));
}
