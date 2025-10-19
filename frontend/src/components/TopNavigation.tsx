import { ArrowLeft } from "lucide-react";

interface TopNavigationProps {
  screen: "configure" | "dashboard";
  // Configure screen props
  configMode?: "random" | "custom" | "auto";
  onConfigModeChange?: (mode: "random" | "custom" | "auto") => void;
  // Dashboard screen props
  dashboardTab?: "stats" | "reviews";
  onDashboardTabChange?: (tab: "stats" | "reviews") => void;
  // Navigation
  onBack?: () => void;
}

export function TopNavigation({ 
  screen, 
  configMode, 
  onConfigModeChange,
  dashboardTab,
  onDashboardTabChange,
  onBack
}: TopNavigationProps) {
  return (
    <header className="fixed top-0 left-0 right-0 px-8 py-5 flex items-center justify-center z-50">
      {onBack && (
        <button
          type="button"
          onClick={onBack}
          className="absolute left-8 top-1/2 -translate-y-1/2 p-2 rounded-full bg-gray-100/70 backdrop-blur-lg border border-gray-300/30 text-gray-600 hover:text-gray-900 hover:bg-gray-200/70 transition-all shadow-sm"
          aria-label="Go back"
        >
          <ArrowLeft className="w-4 h-4" />
        </button>
      )}
      
      {screen === "configure" && configMode && onConfigModeChange && (
        <nav className="flex items-center rounded-full bg-gray-100/70 backdrop-blur-lg border border-gray-300/30 p-0.5 shadow-md shadow-gray-300/20">
          <button
            type="button"
            onClick={() => onConfigModeChange("random")}
            className={`px-3 py-1 rounded-full transition-all whitespace-nowrap ${
              configMode === "random"
                ? "bg-gray-800 text-white shadow-sm"
                : "text-gray-600 hover:text-gray-900"
            }`}
          >
            Random
          </button>
          <button
            type="button"
            onClick={() => onConfigModeChange("custom")}
            className={`px-3 py-1 rounded-full transition-all whitespace-nowrap ${
              configMode === "custom"
                ? "bg-gray-800 text-white shadow-sm"
                : "text-gray-600 hover:text-gray-900"
            }`}
          >
            Custom
          </button>
          <button
            type="button"
            onClick={() => onConfigModeChange("auto")}
            className={`px-3 py-1 rounded-full transition-all whitespace-nowrap ${
              configMode === "auto"
                ? "bg-gray-800 text-white shadow-sm"
                : "text-gray-600 hover:text-gray-900"
            }`}
          >
            Auto
          </button>
        </nav>
      )}

      {screen === "dashboard" && dashboardTab && onDashboardTabChange && (
        <nav className="flex items-center rounded-full bg-gray-100/70 backdrop-blur-lg border border-gray-300/30 p-0.5 shadow-md shadow-gray-300/20">
          <button
            type="button"
            onClick={() => onDashboardTabChange("stats")}
            className={`px-3 py-1 rounded-full transition-all whitespace-nowrap ${
              dashboardTab === "stats"
                ? "bg-gray-800 text-white shadow-sm"
                : "text-gray-600 hover:text-gray-900"
            }`}
          >
            General Statistics
          </button>
          <button
            type="button"
            onClick={() => onDashboardTabChange("reviews")}
            className={`px-3 py-1 rounded-full transition-all whitespace-nowrap ${
              dashboardTab === "reviews"
                ? "bg-gray-800 text-white shadow-sm"
                : "text-gray-600 hover:text-gray-900"
            }`}
          >
            All Reviews
          </button>
        </nav>
      )}
    </header>
  );
}
