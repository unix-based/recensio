import { useState, useEffect } from "react";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export interface Agent {
  id: number;
  name: string;
  age: number;
  gender: "male" | "female";
  occupation: string;
  lifeViews: "progressive" | "moderate" | "conservative";
  innovationAttitude: "conservative" | "moderate" | "innovator";
  riskTolerance: number; // 1-10
  gullibility: number; // 1-10
  emoji: string;
  avatarColor?: string;
  status: "pending" | "reviewing" | "completed";
  ratings?: {
    overall: number;
    clarity: number;
    ux: number;
    valueProposition: number;
  };
  review?: string;
}

export function useAgents(taskId?: string) {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [averages, setAverages] = useState({
    overall: 0,
    clarity: 0,
    ux: 0,
    valueProposition: 0
  });
  const [loading, setLoading] = useState(false);
  const [initialLoad, setInitialLoad] = useState(true);
  const [hasInitialData, setHasInitialData] = useState(false);

  useEffect(() => {
    let pollInterval: NodeJS.Timeout | null = null;
    let isActive = true;

    async function fetchAndSetupLiveData() {
      try {
        setLoading(true);
        
        // Fetch ephemeral agents for current task
        const url = taskId 
          ? `${API_BASE_URL}/api/agents/?task_id=${taskId}`
          : `${API_BASE_URL}/api/agents/`;
        const agentsResponse = await fetch(url);
        
        if (!agentsResponse.ok) {
          throw new Error('Failed to fetch agents');
        }

        const fetchedAgents = await agentsResponse.json();
        
        // Debug: Log initial agent fetch
        console.log(`🚀 Initial fetch: received ${fetchedAgents.length} agents`);
        const completed = fetchedAgents.filter(a => a.status === "completed").length;
        const reviewing = fetchedAgents.filter(a => a.status === "reviewing").length;
        const pending = fetchedAgents.filter(a => a.status === "pending").length;
        console.log(`📊 Initial breakdown: ${completed} completed, ${reviewing} reviewing, ${pending} pending`);
        
        if (isActive) {
          // Use real data from backend - don't override with pending state
          setAgents(fetchedAgents);
          setHasInitialData(true);
          setInitialLoad(false);
          setLoading(false);
          
          // If no agents yet, keep loading state until we get some
          if (fetchedAgents.length === 0) {
            setLoading(true);
          }
        }
        
        // Use polling for live updates
        setupPolling();
        
        function setupPolling() {
          if (isActive && !pollInterval) {
            pollInterval = setInterval(async () => {
              try {
                const url = taskId 
                  ? `${API_BASE_URL}/api/agents/?task_id=${taskId}`
                  : `${API_BASE_URL}/api/agents/`;
                const updatedResponse = await fetch(url);
                if (updatedResponse.ok && isActive) {
                  const updatedAgents = await updatedResponse.json();
                  
                  // Debug: Log agent count and status breakdown
                  console.log(`🔄 Polling agents: received ${updatedAgents.length} agents`);
                  const completed = updatedAgents.filter(a => a.status === "completed").length;
                  const reviewing = updatedAgents.filter(a => a.status === "reviewing").length;
                  const pending = updatedAgents.filter(a => a.status === "pending").length;
                  console.log(`📊 Agent breakdown: ${completed} completed, ${reviewing} reviewing, ${pending} pending`);
                  
                  // Update with new data from backend
                  if (hasInitialData) {
                    setAgents(prevAgents => {
                      const hasChanges = JSON.stringify(prevAgents) !== JSON.stringify(updatedAgents);
                      if (hasChanges) {
                        // Use new data from backend - this includes progressive updates
                        setLoading(false); // Stop loading when we get data
                        return updatedAgents;
                      }
                      return prevAgents;
                    });
                  } else {
                    // First time getting data
                    setAgents(updatedAgents);
                    setLoading(false);
                    setHasInitialData(true);
                  }
                }
              } catch (error) {
                console.error('Error polling agents:', error);
              }
            }, 2000); // Poll every 2 seconds for more responsive updates
          }
        }
        
      } catch (error) {
        console.error('Error fetching agents:', error);
        if (isActive) {
          setAgents([]);
          setLoading(false);
        }
      }
    }


    fetchAndSetupLiveData();

    // Cleanup function
    return () => {
      isActive = false;
      if (pollInterval) {
        clearInterval(pollInterval);
      }
    };
  }, [taskId]);

  // Calculate averages whenever agents update
  useEffect(() => {
    const completedAgents = agents.filter(a => a.status === "completed" && a.ratings);
    if (completedAgents.length === 0) return;

    const sums = completedAgents.reduce(
      (acc, agent) => ({
        overall: acc.overall + (agent.ratings?.overall || 0),
        clarity: acc.clarity + (agent.ratings?.clarity || 0),
        ux: acc.ux + (agent.ratings?.ux || 0),
        valueProposition: acc.valueProposition + (agent.ratings?.valueProposition || 0),
      }),
      { overall: 0, clarity: 0, ux: 0, valueProposition: 0 }
    );

    setAverages({
      overall: sums.overall / completedAgents.length,
      clarity: sums.clarity / completedAgents.length,
      ux: sums.ux / completedAgents.length,
      valueProposition: sums.valueProposition / completedAgents.length,
    });
  }, [agents]);

  return { agents, averages, loading, initialLoad };
}
