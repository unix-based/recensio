import React, { useState, useMemo } from "react";
import { motion } from "motion/react";
import { Agent } from "../hooks/useAgents";
import { AgentDialog } from "./AgentDialog";
import { ChatDialog } from "./ChatDialog";
import { Popover, PopoverContent, PopoverTrigger } from "./ui/popover";
import { Button } from "./ui/button";
import { MessageCircle } from "lucide-react";

interface UserMapProps {
  agents: Agent[];
}

export function UserMap({ agents }: UserMapProps) {
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [chatOpen, setChatOpen] = useState(false);
  const [chatAgent, setChatAgent] = useState<Agent | null>(null);
  const [hoveredAgentId, setHoveredAgentId] = useState<number | null>(null);

  const handleAgentClick = (agent: Agent) => {
    // Allow clicking on any agent, but only show dialog for completed ones
    if (agent.status === "completed") {
      setSelectedAgent(agent);
      setDialogOpen(true);
    }
    // For pending/reviewing agents, we could show a different message or do nothing
  };

  const handleChatClick = (agent: Agent, e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent triggering agent click
    setChatAgent(agent);
    setChatOpen(true);
  };

  // Memoize random positions for pending agents to avoid re-renders
  const randomPositions = useMemo(() => {
    const positions: Record<number, { x: number; y: number }> = {};
    agents.forEach(agent => {
      positions[agent.id] = {
        x: Math.random() * 90 + 5, // Keep within 5-95% to avoid edges
        y: Math.random() * 90 + 5
      };
    });
    return positions;
  }, [agents.length]);

  // Position agents on a 2D map based on clarity (x) and value proposition (y)
  const getAgentPosition = (agent: Agent) => {
    if (!agent.ratings) {
      // Use memoized random position for pending agents
      return randomPositions[agent.id];
    }

    // Map ratings (0-100) to position percentage (with padding)
    return {
      x: Math.max(5, Math.min(95, agent.ratings.clarity)),
      y: Math.max(5, Math.min(95, 100 - agent.ratings.valueProposition)) // Invert Y so high values are at top
    };
  };


  return (
    <>
      {/* Map container - Full width */}
      <div className="relative w-full h-[500px] bg-gradient-to-br from-gray-50 via-white to-blue-50/30 rounded-lg overflow-hidden" 
           style={{ boxShadow: 'inset 0 0 0 1px rgba(229, 231, 235, 0.8)' }}>
        {/* Subtle grid background */}
        <div className="absolute inset-0">
          {/* Light grid pattern */}
          <div className="absolute inset-0 opacity-30" style={{
            backgroundImage: `
              linear-gradient(to right, #e5e7eb 1px, transparent 1px),
              linear-gradient(to bottom, #e5e7eb 1px, transparent 1px)
            `,
            backgroundSize: '10% 10%'
          }} />
          
          {/* Subtle radial gradient */}
          <div className="absolute inset-0 bg-gradient-radial from-blue-50/20 via-transparent to-transparent" />
        </div>

        {/* Agents - show all agents */}
        {agents.map((agent) => {
        // Show all agents, but handle different statuses appropriately

        const pos = getAgentPosition(agent);
        
        // Get color based on rating
        const getScoreColor = (score: number) => {
          if (score >= 71) return "from-teal-400 to-teal-500";
          if (score >= 41) return "from-amber-400 to-amber-500";
          return "from-orange-400 to-orange-500";
        };

        // Get color based on status and ratings
        let scoreColor: string;
        if (agent.status === "completed" && agent.ratings) {
          scoreColor = getScoreColor(agent.ratings.overall);
        } else if (agent.status === "reviewing") {
          scoreColor = "from-blue-400 to-blue-500"; // Blue for reviewing
        } else {
          scoreColor = "from-gray-400 to-gray-500"; // Gray for pending
        }

        return (
          <Popover key={agent.id} open={hoveredAgentId === agent.id} onOpenChange={(open) => !open && setHoveredAgentId(null)}>
            <PopoverTrigger asChild>
              <motion.button
                type="button"
                initial={{ scale: 0, opacity: 0 }}
                animate={{ 
                  scale: 1,
                  opacity: 1,
                }}
                whileHover={{ scale: 1.8 }}
                transition={{ type: "spring", stiffness: 300, damping: 25 }}
                onClick={() => handleAgentClick(agent)}
                onMouseEnter={() => setHoveredAgentId(agent.id)}
                onMouseLeave={() => setHoveredAgentId(null)}
                className={`absolute -translate-x-1/2 -translate-y-1/2 w-3 h-3 rounded-full bg-gradient-to-br ${scoreColor} cursor-pointer shadow-md border-0`}
                style={{
                  left: `${pos.x}%`,
                  top: `${pos.y}%`,
                }}
              />
            </PopoverTrigger>
            <PopoverContent 
              className="w-72 p-0 overflow-hidden bg-white border-gray-200 shadow-lg" 
              side="top"
              sideOffset={12}
              onMouseEnter={() => setHoveredAgentId(agent.id)}
              onMouseLeave={() => setHoveredAgentId(null)}
            >
              <div className="space-y-0">
                {/* Agent Info - Compact */}
                <div className="p-3 space-y-2">
                  <div className="flex items-center gap-2">
                    <span className="text-2xl">{agent.emoji}</span>
                    <div className="flex-1 min-w-0">
                      <h4 className="text-sm text-gray-900 truncate">{agent.name}</h4>
                      <p className="text-xs text-gray-500 truncate">{agent.occupation}</p>
                    </div>
                  </div>
                  
                  {/* Review - Moved above ratings */}
                  {agent.review && (
                    <div className="bg-gray-50 p-2 rounded-md">
                      <p className="text-xs text-gray-600 italic leading-relaxed">
                        "{agent.review}"
                      </p>
                    </div>
                  )}
                  
                  {/* Status indicator for non-completed agents */}
                  {agent.status !== "completed" && (
                    <div className="bg-blue-50 p-2 rounded-md">
                      <p className="text-xs text-blue-600 font-medium">
                        {agent.status === "reviewing" ? "🔄 Reviewing..." : "⏳ Pending..."}
                      </p>
                    </div>
                  )}
                  
                  {/* Ratings - Compact */}
                  {agent.ratings && (
                    <div className="space-y-2">
                      {/* Overall Rating - Made more prominent */}
                      <div className="flex items-center gap-2 p-2 bg-blue-50 rounded-md">
                        <span className="text-xs font-semibold text-blue-700 w-12">Overall</span>
                        <div className="flex-1 h-2 bg-blue-100 rounded-full overflow-hidden">
                          <motion.div
                            className={`h-full bg-gradient-to-r from-blue-500 to-blue-600 rounded-full`}
                            initial={{ width: 0 }}
                            animate={{ width: `${agent.ratings.overall}%` }}
                            transition={{ duration: 0.6, ease: "easeOut" }}
                          />
                        </div>
                        <span className="text-xs font-bold text-blue-900 w-6 text-right">{agent.ratings.overall}</span>
                      </div>

                      {/* Clarity */}
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-gray-500 w-12">Clarity</span>
                        <div className="flex-1 h-1 bg-gray-100 rounded-full overflow-hidden">
                          <motion.div
                            className={`h-full bg-gradient-to-r ${getScoreColor(agent.ratings.clarity)} opacity-70 rounded-full`}
                            initial={{ width: 0 }}
                            animate={{ width: `${agent.ratings.clarity}%` }}
                            transition={{ duration: 0.6, ease: "easeOut", delay: 0.1 }}
                          />
                        </div>
                        <span className="text-xs text-gray-700 w-6 text-right">{agent.ratings.clarity}</span>
                      </div>

                      {/* UX */}
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-gray-500 w-12">UX</span>
                        <div className="flex-1 h-1 bg-gray-100 rounded-full overflow-hidden">
                          <motion.div
                            className={`h-full bg-gradient-to-r ${getScoreColor(agent.ratings.ux)} opacity-70 rounded-full`}
                            initial={{ width: 0 }}
                            animate={{ width: `${agent.ratings.ux}%` }}
                            transition={{ duration: 0.6, ease: "easeOut", delay: 0.2 }}
                          />
                        </div>
                        <span className="text-xs text-gray-700 w-6 text-right">{agent.ratings.ux}</span>
                      </div>

                      {/* Value */}
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-gray-500 w-12">Value</span>
                        <div className="flex-1 h-1 bg-gray-100 rounded-full overflow-hidden">
                          <motion.div
                            className={`h-full bg-gradient-to-r ${getScoreColor(agent.ratings.valueProposition)} opacity-70 rounded-full`}
                            initial={{ width: 0 }}
                            animate={{ width: `${agent.ratings.valueProposition}%` }}
                            transition={{ duration: 0.6, ease: "easeOut", delay: 0.3 }}
                          />
                        </div>
                        <span className="text-xs text-gray-700 w-6 text-right">{agent.ratings.valueProposition}</span>
                      </div>
                    </div>
                  )}
                </div>
                
                <div className="bg-gray-50/50 px-3 py-2 border-t border-gray-100">
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-xs text-gray-400">
                      {agent.status === "completed" ? "Click for full profile" : "Profile will be available when review completes"}
                    </p>
                    {agent.status === "completed" && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => handleChatClick(agent, e)}
                        className="h-6 px-2 text-xs hover:bg-blue-50 hover:text-blue-600"
                      >
                        <MessageCircle className="w-3 h-3 mr-1" />
                        Chat
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            </PopoverContent>
          </Popover>
        );
      })}
      </div>

      <AgentDialog
        agent={selectedAgent}
        open={dialogOpen}
        onOpenChange={setDialogOpen}
      />
      
      <ChatDialog
        agent={chatAgent}
        open={chatOpen}
        onOpenChange={setChatOpen}
      />
    </>
  );
}