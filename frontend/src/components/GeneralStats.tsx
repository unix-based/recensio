import { useState, useEffect, useMemo } from "react";
import { motion, useSpring, useTransform } from "motion/react";
import { Agent } from "../hooks/useAgents";
import { TrendingDown, TrendingUp, MessageSquare } from "lucide-react";
import { extractPainPoints, extractLikedFeatures } from "../lib/reviewAnalysis";
import { ReviewDialog } from "./ReviewDialog";
import { UserMap } from "./UserMap";

function AnimatedNumber({ value, isPrimary, isLoading }: { value: number; isPrimary: boolean; isLoading: boolean }) {
  const spring = useSpring(0, { 
    stiffness: 50, 
    damping: 30,
    mass: 1
  });
  const display = useTransform(spring, (latest) => Math.round(latest).toFixed(0));

  useEffect(() => {
    spring.set(value);
  }, [spring, value]);

  return (
    <motion.span
      className="text-gray-900 tabular-nums"
      style={isPrimary ? { fontSize: '3rem', lineHeight: '1', fontWeight: '500' } : { fontSize: '1.25rem', fontWeight: '500' }}
    >
      {isLoading ? "—" : display}
    </motion.span>
  );
}

function UnifiedRatingCard({ averages, isLoading }: { 
  averages: { overall: number; clarity: number; ux: number; valueProposition: number }; 
  isLoading: boolean 
}) {
  const metrics = [
    { label: "Overall", value: averages.overall, isPrimary: true },
    { label: "Clarity", value: averages.clarity, isPrimary: false },
    { label: "UX/Design", value: averages.ux, isPrimary: false },
    { label: "Value Proposition", value: averages.valueProposition, isPrimary: false },
  ];

  const getBarGradient = (value: number) => {
    if (value >= 71) return "from-teal-400 to-teal-500";
    if (value >= 41) return "from-amber-400 to-amber-500";
    return "from-orange-400 to-orange-500";
  };

  return (
    <div className="space-y-8 pr-8">
      {metrics.map((metric, index) => (
        <div key={metric.label} className={metric.isPrimary ? "pb-8" : ""}>
          <div className="flex items-baseline justify-between mb-3">
            <p className={`text-gray-400 ${metric.isPrimary ? 'text-xs uppercase tracking-wider' : 'text-xs'}`}>
              {metric.label}
            </p>
            <div className="flex items-baseline gap-2">
              <AnimatedNumber value={metric.value} isPrimary={metric.isPrimary} isLoading={isLoading} />
              {!metric.isPrimary && <span className="text-gray-300 text-xs">/ 100</span>}
            </div>
          </div>
          
          {/* Animated bar */}
          <div className="relative h-2 bg-gray-100 rounded-full overflow-hidden">
            <motion.div
              initial={{ width: 0, opacity: 0 }}
              animate={{ 
                width: isLoading ? "0%" : `${metric.value}%`,
                opacity: isLoading ? 0 : 1
              }}
              transition={{ 
                width: { duration: 1.5, ease: [0.25, 0.1, 0.25, 1], delay: index * 0.1 },
                opacity: { duration: 1, delay: index * 0.1 }
              }}
              className={`h-full rounded-full bg-gradient-to-r ${getBarGradient(metric.value)}`}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

interface GeneralStatsProps {
  agents: Agent[];
  averages: {
    overall: number;
    clarity: number;
    ux: number;
    valueProposition: number;
  };
}

export function GeneralStats({ agents, averages }: GeneralStatsProps) {
  const [selectedReviewItem, setSelectedReviewItem] = useState<{
    type: "pain" | "feature";
    text: string;
    reviews: Array<{ agent: Agent; review: string }>;
  } | null>(null);

  const completedAgents = agents.filter(a => a.status === "completed");
  const completedCount = completedAgents.length;
  const isLoading = completedCount === 0;

  // Extract pain points and liked features
  const painPoints = useMemo(() => extractPainPoints(agents), [agents]);
  const likedFeatures = useMemo(() => extractLikedFeatures(agents), [agents]);

  // Show loading state when no agents yet
  if (agents.length === 0) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center space-y-4">
          <div className="flex justify-center">
            <div className="flex space-x-1">
              <motion.div
                className="w-3 h-3 bg-blue-500 rounded-full"
                animate={{ scale: [1, 1.2, 1] }}
                transition={{ duration: 0.6, repeat: Infinity, delay: 0 }}
              />
              <motion.div
                className="w-3 h-3 bg-blue-500 rounded-full"
                animate={{ scale: [1, 1.2, 1] }}
                transition={{ duration: 0.6, repeat: Infinity, delay: 0.2 }}
              />
              <motion.div
                className="w-3 h-3 bg-blue-500 rounded-full"
                animate={{ scale: [1, 1.2, 1] }}
                transition={{ duration: 0.6, repeat: Infinity, delay: 0.4 }}
              />
            </div>
          </div>
          <div>
            <h3 className="text-lg font-medium text-gray-900">Initializing AI Agents</h3>
            <p className="text-gray-500 mt-1">Generating diverse user profiles and launching reviews...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="space-y-8">
        {/* Rating and Map Section - Side by Side */}
        <div className="flex gap-8">
          {/* Rating Section - Left Half */}
          <div className="flex-1">
            <UnifiedRatingCard averages={averages} isLoading={isLoading} />
          </div>

          {/* User Map - Right Half */}
          <div className="flex-1">
            <UserMap agents={agents} />
          </div>
        </div>

        {/* Pain Points and Liked Features - Parallel */}
        <div className="flex gap-4 pt-4">
          {/* Pain Points */}
          <div className="flex-1 bg-gradient-to-br from-orange-50/30 to-white rounded-xl p-4">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-5 h-5 rounded-md bg-gradient-to-br from-orange-100 to-orange-200 flex items-center justify-center">
                <TrendingDown className="w-3 h-3 text-orange-600" />
              </div>
              <h3 className="text-gray-400 text-xs uppercase tracking-wider">Most Mentioned Pain Points</h3>
            </div>
            <div className="space-y-6">
              {painPoints.length === 0 ? (
                <div className="text-center py-3 text-gray-400 text-xs">
                  No pain points identified yet
                </div>
              ) : (
                <>
                  {painPoints.slice(0, 3).map((point, index) => (
                    <div
                      key={index}
                      onClick={() => setSelectedReviewItem({ type: "pain", text: point.text, reviews: point.reviews })}
                      className="group cursor-pointer"
                    >
                      <div className="flex items-baseline justify-between mb-3">
                        <p className="text-gray-400 group-hover:text-gray-900 text-xs tracking-wider transition-colors">
                          {point.text}
                        </p>
                        <div className="flex items-baseline gap-2 ml-4">
                          <span className="text-gray-400 group-hover:text-gray-900 tabular-nums transition-colors">{point.mentions}</span>
                          <MessageSquare className="w-3 h-3 text-orange-400 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0" />
                        </div>
                      </div>
                      
                      {/* Animated bar */}
                      <div className="relative h-2 bg-gray-100 rounded-full overflow-hidden">
                        <motion.div
                          initial={{ width: 0, opacity: 0 }}
                          animate={{ 
                            width: `${point.percentage}%`,
                            opacity: 1
                          }}
                          transition={{ 
                            width: { duration: 1.5, ease: [0.25, 0.1, 0.25, 1], delay: index * 0.1 },
                            opacity: { duration: 1, delay: index * 0.1 }
                          }}
                          className="h-full rounded-full bg-gradient-to-r from-orange-400 to-orange-500 group-hover:from-orange-500 group-hover:to-orange-400 transition-all duration-300"
                        />
                      </div>
                    </div>
                  ))}
                </>
              )}
            </div>
          </div>

          {/* Liked Features */}
          <div className="flex-1 bg-gradient-to-br from-teal-50/30 to-white rounded-xl p-4">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-5 h-5 rounded-md bg-gradient-to-br from-teal-100 to-teal-200 flex items-center justify-center">
                <TrendingUp className="w-3 h-3 text-teal-600" />
              </div>
              <h3 className="text-gray-400 text-xs uppercase tracking-wider">Features Users Like Most</h3>
            </div>
            <div className="space-y-6">
              {likedFeatures.length === 0 ? (
                <div className="text-center py-3 text-gray-400 text-xs">
                  No liked features identified yet
                </div>
              ) : (
                <>
                  {likedFeatures.slice(0, 3).map((feature, index) => (
                    <div
                      key={index}
                      onClick={() => setSelectedReviewItem({ type: "feature", text: feature.text, reviews: feature.reviews })}
                      className="group cursor-pointer"
                    >
                      <div className="flex items-baseline justify-between mb-3">
                        <p className="text-gray-400 group-hover:text-gray-900 text-xs tracking-wider transition-colors">
                          {feature.text}
                        </p>
                        <div className="flex items-baseline gap-2 ml-4">
                          <span className="text-gray-400 group-hover:text-gray-900 tabular-nums transition-colors">{feature.mentions}</span>
                          <MessageSquare className="w-3 h-3 text-teal-400 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0" />
                        </div>
                      </div>
                      
                      {/* Animated bar */}
                      <div className="relative h-2 bg-gray-100 rounded-full overflow-hidden">
                        <motion.div
                          initial={{ width: 0, opacity: 0 }}
                          animate={{ 
                            width: `${feature.percentage}%`,
                            opacity: 1
                          }}
                          transition={{ 
                            width: { duration: 1.5, ease: [0.25, 0.1, 0.25, 1], delay: index * 0.1 },
                            opacity: { duration: 1, delay: index * 0.1 }
                          }}
                          className="h-full rounded-full bg-gradient-to-r from-teal-400 to-teal-500 group-hover:from-teal-500 group-hover:to-teal-400 transition-all duration-300"
                        />
                      </div>
                    </div>
                  ))}
                </>
              )}
            </div>
          </div>
        </div>
      </div>

      <ReviewDialog
        open={selectedReviewItem !== null}
        onOpenChange={() => setSelectedReviewItem(null)}
        selectedItem={selectedReviewItem}
      />
    </>
  );
}