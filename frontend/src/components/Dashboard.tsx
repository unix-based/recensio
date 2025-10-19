import { useState } from "react";
import { motion } from "motion/react";
import { GeneralStats } from "./GeneralStats";
import { AllReviews } from "./AllReviews";
import { useAgents } from "../hooks/useAgents";

interface DashboardProps {
  websiteUrl: string;
  activeTab: "stats" | "reviews";
  taskStatus?: any;
}

export function Dashboard({ websiteUrl, activeTab, taskStatus }: DashboardProps) {
  const taskId = taskStatus?.task_id;
  const { agents, averages, loading, initialLoad } = useAgents(taskId);
  
  const completedAgents = agents.filter(a => a.status === "completed");
  const reviewingAgents = agents.filter(a => a.status === "reviewing");
  const pendingAgents = agents.filter(a => a.status === "pending");

  return (
    <div className="w-full min-h-screen">


      {/* Tab content */}
      <div className={activeTab === "stats" ? "max-w-7xl mx-auto pb-12 px-6" : "max-w-7xl ml-auto mr-12 pb-12 px-6"}>
        {activeTab === "stats" ? (
          <GeneralStats agents={agents} averages={averages} />
        ) : (
          <AllReviews agents={agents} />
        )}
      </div>
    </div>
  );
}
