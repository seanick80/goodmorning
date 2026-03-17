import { useState } from "react";
import Dashboard from "./components/Dashboard";
import WidgetMockSwitcher from "./components/mocks/widget-mocks/WidgetMockSwitcher";

// Toggle between Dashboard and WidgetMockSwitcher for design review.
// Set initial view to "mocks" to browse widget variants,
// or "dashboard" to use the live dashboard.
const INITIAL_VIEW = "mocks";

export default function App() {
  const [view, setView] = useState(INITIAL_VIEW);

  if (view === "mocks") {
    return <WidgetMockSwitcher onBack={() => setView("dashboard")} />;
  }

  return <Dashboard />;
}
