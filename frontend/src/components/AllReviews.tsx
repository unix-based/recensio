import { useState, useMemo } from "react";
import { motion } from "motion/react";
import { Agent } from "../hooks/useAgents";
import { AgentDialog } from "./AgentDialog";
import { ArrowUpDown, ArrowUp, ArrowDown } from "lucide-react";

interface AllReviewsProps {
  agents: Agent[];
}

type SortOption = "default" | "rating-high" | "rating-low" | "name-asc" | "name-desc";

export function AllReviews({ agents }: AllReviewsProps) {
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [sortBy, setSortBy] = useState<SortOption>("default");

  // Sort completed agents based on selected option
  const sortedCompletedAgents = useMemo(() => {
    const filtered = agents.filter(a => a.status === "completed");
    
    switch (sortBy) {
      case "rating-high":
        return [...filtered].sort((a, b) => (b.ratings?.overall || 0) - (a.ratings?.overall || 0));
      case "rating-low":
        return [...filtered].sort((a, b) => (a.ratings?.overall || 0) - (b.ratings?.overall || 0));
      case "name-asc":
        return [...filtered].sort((a, b) => a.name.localeCompare(b.name));
      case "name-desc":
        return [...filtered].sort((a, b) => b.name.localeCompare(a.name));
      case "default":
      default:
        return filtered;
    }
  }, [agents, sortBy]);

  const getScoreColorDot = (score: number) => {
    if (score >= 71) return "bg-teal-500";
    if (score >= 41) return "bg-amber-500";
    return "bg-orange-500";
  };

  return (
    <>
      <div className="space-y-6">
        {/* Header with sort controls */}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-gray-900">All Reviews</h2>
            <p className="text-sm text-gray-500 mt-1">
              {sortedCompletedAgents.length} {sortedCompletedAgents.length === 1 ? 'review' : 'reviews'} from AI agents
            </p>
          </div>
          
          {/* Sort buttons */}
          <div className="flex items-center gap-1">
            <button
              onClick={() => setSortBy(sortBy === "rating-high" ? "rating-low" : "rating-high")}
              className={`px-2 py-1 text-xs rounded transition-colors ${
                sortBy === "rating-high" || sortBy === "rating-low"
                  ? "bg-gray-200 text-gray-900"
                  : "text-gray-400 hover:bg-gray-100 hover:text-gray-600"
              }`}
              title={sortBy === "rating-high" ? "Rating: High to Low" : "Rating: Low to High"}
            >
              <div className="flex items-center gap-1">
                <span>Rating</span>
                {sortBy === "rating-high" ? (
                  <ArrowDown className="h-3 w-3" />
                ) : sortBy === "rating-low" ? (
                  <ArrowUp className="h-3 w-3" />
                ) : (
                  <ArrowUpDown className="h-3 w-3" />
                )}
              </div>
            </button>
            
            <button
              onClick={() => setSortBy(sortBy === "name-asc" ? "name-desc" : "name-asc")}
              className={`px-2 py-1 text-xs rounded transition-colors ${
                sortBy === "name-asc" || sortBy === "name-desc"
                  ? "bg-gray-200 text-gray-900"
                  : "text-gray-400 hover:bg-gray-100 hover:text-gray-600"
              }`}
              title={sortBy === "name-asc" ? "Name: A to Z" : "Name: Z to A"}
            >
              <div className="flex items-center gap-1">
                <span>Name</span>
                {sortBy === "name-asc" ? (
                  <ArrowUp className="h-3 w-3" />
                ) : sortBy === "name-desc" ? (
                  <ArrowDown className="h-3 w-3" />
                ) : (
                  <ArrowUpDown className="h-3 w-3" />
                )}
              </div>
            </button>
            
            {sortBy !== "default" && (
              <button
                onClick={() => setSortBy("default")}
                className="px-2 py-1 text-xs text-gray-400 hover:text-gray-600 transition-colors"
                title="Reset sorting"
              >
                Reset
              </button>
            )}
          </div>
        </div>
        
        {/* Reviews grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {sortedCompletedAgents.length === 0 ? (
            <div className="col-span-full flex items-center justify-center h-64 text-gray-400 text-sm">
              <div className="text-center space-y-2">
                <p>No completed reviews yet</p>
                <p className="text-xs">Agents are working on their evaluations...</p>
              </div>
            </div>
          ) : (
            sortedCompletedAgents.map((agent, index) => {
              return (
                <motion.button
                  key={agent.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ 
                    duration: 0.5, 
                    delay: index * 0.1,
                    ease: "easeOut"
                  }}
                  onClick={() => {
                    setSelectedAgent(agent);
                    setDialogOpen(true);
                  }}
                  className="w-full text-left p-3 rounded-lg border border-gray-200 hover:border-gray-300 hover:shadow-sm transition-all bg-white"
                >
                  <div className="space-y-2">
                    {/* Agent header */}
                    <div className="flex items-start gap-2">
                      <span className="text-lg">{agent.emoji}</span>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <h4 className="text-sm text-gray-900 truncate">{agent.name}</h4>
                          {agent.ratings && (
                            <div className="flex items-center gap-1">
                              <div className={`w-1.5 h-1.5 rounded-full ${getScoreColorDot(agent.ratings.overall)}`} />
                              <span className="text-xs text-gray-500">{agent.ratings.overall}</span>
                            </div>
                          )}
                        </div>
                        <p className="text-xs text-gray-500 truncate">{agent.occupation}</p>
                      </div>
                    </div>

                    {/* Review */}
                    {agent.review && (
                      <p className="text-xs text-gray-600 line-clamp-3 leading-relaxed">
                        "{agent.review}"
                      </p>
                    )}
                  </div>
                </motion.button>
              );
            })
          )}
        </div>
      </div>

      <AgentDialog
        agent={selectedAgent}
        open={dialogOpen}
        onOpenChange={setDialogOpen}
      />
    </>
  );
}