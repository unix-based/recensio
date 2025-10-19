import { Agent } from "../hooks/useAgents";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "./ui/dialog";

interface AgentDialogProps {
  agent: Agent | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function AgentDialog({ agent, open, onOpenChange }: AgentDialogProps) {
  if (!agent) return null;

  const getScoreColor = (score: number) => {
    if (score >= 71) return "from-teal-400 to-teal-500";
    if (score >= 41) return "from-amber-400 to-amber-500";
    return "from-orange-400 to-orange-500";
  };

  const overallScore = agent.ratings?.overall || 0;
  const scoreGradient = getScoreColor(overallScore);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-3">
            <div className={`w-12 h-12 rounded-full bg-gradient-to-br ${scoreGradient} flex items-center justify-center shrink-0 border-2 border-white/20 shadow-lg`}>
              <span className="text-2xl">{agent.emoji}</span>
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-gray-900">{agent.name}</div>
              <div className="text-xs text-gray-500">{agent.occupation}</div>
            </div>
          </DialogTitle>
          <DialogDescription className="sr-only">
            Agent profile and review details for {agent.name}
          </DialogDescription>
        </DialogHeader>
        
        <div className="space-y-3 pt-2">
          {/* Review Section */}
          {agent.review && (
            <div className="bg-gradient-to-br from-gray-50 to-white p-3 rounded-lg border border-gray-100">
              <p className="text-xs text-gray-600 italic leading-relaxed">"{agent.review}"</p>
            </div>
          )}

          {/* Ratings Section */}
          {agent.ratings && (
            <div className="space-y-2">
              <p className="text-xs text-gray-500 uppercase tracking-wider">Ratings</p>
              <div className="grid grid-cols-2 gap-2">
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-500 w-16">Overall</span>
                  <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div className={`h-full bg-gradient-to-r ${getScoreColor(agent.ratings.overall)}`} 
                         style={{ width: `${agent.ratings.overall}%` }} />
                  </div>
                  <span className="text-xs text-gray-900 w-6 text-right">{agent.ratings.overall}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-500 w-16">Clarity</span>
                  <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div className={`h-full bg-gradient-to-r ${getScoreColor(agent.ratings.clarity)}`} 
                         style={{ width: `${agent.ratings.clarity}%` }} />
                  </div>
                  <span className="text-xs text-gray-900 w-6 text-right">{agent.ratings.clarity}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-500 w-16">UX/Design</span>
                  <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div className={`h-full bg-gradient-to-r ${getScoreColor(agent.ratings.ux)}`} 
                         style={{ width: `${agent.ratings.ux}%` }} />
                  </div>
                  <span className="text-xs text-gray-900 w-6 text-right">{agent.ratings.ux}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-500 w-16">Value Prop</span>
                  <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div className={`h-full bg-gradient-to-r ${getScoreColor(agent.ratings.valueProposition)}`} 
                         style={{ width: `${agent.ratings.valueProposition}%` }} />
                  </div>
                  <span className="text-xs text-gray-900 w-6 text-right">{agent.ratings.valueProposition}</span>
                </div>
              </div>
            </div>
          )}

          {/* Agent Details - Compact Grid */}
          <div className="border-t pt-3">
            <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">Profile</p>
            <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-gray-500">Age</span>
                <span className="text-gray-900">{agent.age}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Gender</span>
                <span className="text-gray-900 capitalize">{agent.gender}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Life Views</span>
                <span className="text-gray-900 capitalize">{agent.lifeViews}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Innovation</span>
                <span className="text-gray-900 capitalize">{agent.innovationAttitude}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Risk Tolerance</span>
                <span className="text-gray-900">{agent.riskTolerance}/10</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Gullibility</span>
                <span className="text-gray-900">{agent.gullibility}/10</span>
              </div>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
