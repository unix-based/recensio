import { useState, useEffect } from "react";
import { Header } from "./components/Header";
import { TopNavigation } from "./components/TopNavigation";
import { SearchBar } from "./components/SearchBar";
import { AgentConfiguration } from "./components/AgentConfiguration";
import { Dashboard } from "./components/Dashboard";

type Screen = "search" | "configure" | "dashboard";

interface AgentFilters {
  ageRange: [number, number];
  gender: string;
  occupation: string;
  lifeViews: string;
  innovationAttitude: string;
  riskTolerance: number;
  gullibility: number;
}

export default function App() {
  const [currentScreen, setCurrentScreen] = useState<Screen>("search");
  const [validatedUrl, setValidatedUrl] = useState("");
  const [configMode, setConfigMode] = useState<"random" | "custom" | "auto">("random");
  const [dashboardTab, setDashboardTab] = useState<"stats" | "reviews">("stats");
  const [taskId, setTaskId] = useState<string | null>(null);
  const [taskStatus, setTaskStatus] = useState<any>(null);

  const handleUrlValidated = (url: string) => {
    setValidatedUrl(url);
    setCurrentScreen("configure");
  };

  const handleGenerateAgents = (filters: AgentFilters, mode?: string) => {
    console.log("Generating agents with:", { filters, mode });
    
    // Navigate to dashboard immediately - no waiting
    setCurrentScreen("dashboard");
    
    // Start background task (fire and forget - don't care if it fails)
    setTimeout(() => {
      startAIAgentsBackground(filters, mode);
    }, 0);
  };

  const startAIAgentsBackground = async (filters: AgentFilters, mode?: string) => {
    try {
      // Determine target audience based on mode
      let target_audience = null;
      if (mode === "custom") {
        target_audience = {
          ageRange: filters.ageRange,
          gender: filters.gender || "any",
          occupation: filters.occupation || "varied professionals",
          lifeViews: filters.lifeViews || "varied",
          innovationAttitude: filters.innovationAttitude || "varied",
          riskTolerance: filters.riskTolerance,
          gullibility: filters.gullibility
        };
      }
      
      // Start background AI agents task - don't block anything
      fetch('http://localhost:8000/api/agents/ai-launch', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          website_url: validatedUrl,
          target_audience: target_audience
        })
      }).then(response => {
        if (response.ok) {
          response.json().then(result => {
            console.log("AI agents started in background:", result);
            // Set the task ID so polling can start and Dashboard gets the taskStatus
            setTaskId(result.task_id);
            setTaskStatus(result);
          });
        }
      }).catch(error => {
        console.log("AI agents failed (doesn't matter):", error);
      });
      
    } catch (error) {
      console.log("AI agents error (doesn't matter):", error);
    }
  };

  // Poll for task status updates
  useEffect(() => {
    if (!taskId) return;

    const pollInterval = setInterval(async () => {
      try {
        const response = await fetch(`http://localhost:8000/api/agents/ai-status/${taskId}`);
        if (response.ok) {
          const status = await response.json();
          setTaskStatus(status);
          
          console.log("Task status update:", status);
          
          // Stop polling if task is completed or failed
          if (status.status === "completed" || status.status === "failed") {
            clearInterval(pollInterval);
          }
        }
      } catch (error) {
        console.error('Error polling task status:', error);
      }
    }, 2000); // Poll every 2 seconds

    return () => clearInterval(pollInterval);
  }, [taskId]);


  const handleBack = () => {
    if (currentScreen === "dashboard") {
      setCurrentScreen("configure");
    } else if (currentScreen === "configure") {
      setCurrentScreen("search");
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-blue-50/30 relative overflow-hidden">
      {/* Subtle background decoration */}
      <div className="absolute inset-0 opacity-[0.03]">
        <div className="absolute top-20 left-10 w-96 h-96 bg-blue-500 rounded-full blur-3xl"></div>
        <div className="absolute bottom-20 right-10 w-96 h-96 bg-purple-500 rounded-full blur-3xl"></div>
      </div>
      
      {currentScreen === "search" ? (
        <Header />
      ) : currentScreen === "configure" ? (
        <TopNavigation 
          screen="configure"
          configMode={configMode}
          onConfigModeChange={setConfigMode}
          onBack={handleBack}
        />
      ) : (
        <TopNavigation 
          screen="dashboard"
          dashboardTab={dashboardTab}
          onDashboardTabChange={setDashboardTab}
          onBack={handleBack}
        />
      )}
      
      {currentScreen === "search" ? (
        <main className="min-h-screen flex flex-col items-center justify-center px-6 relative z-10">
          <div className="flex flex-col items-center gap-12 w-full">
            <h2 className="text-5xl text-gradient-light leading-tight pb-2">What they really think?</h2>
            <SearchBar onValidated={handleUrlValidated} />
          </div>
        </main>
      ) : currentScreen === "configure" ? (
        <main className="min-h-screen flex flex-col items-center justify-center px-6 pt-20 relative z-10">
          <div className="flex flex-col items-center gap-8 w-full">
            <AgentConfiguration 
              websiteUrl={validatedUrl}
              mode={configMode}
              onGenerate={handleGenerateAgents}
              onModeChange={setConfigMode}
            />
          </div>
        </main>
      ) : (
        <main className="min-h-screen pt-20 relative z-10">
          <Dashboard 
            websiteUrl={validatedUrl} 
            activeTab={dashboardTab}
            taskStatus={taskStatus}
          />
        </main>
      )}
    </div>
  );
}
