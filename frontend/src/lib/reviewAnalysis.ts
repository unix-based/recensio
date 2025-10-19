import { Agent } from "../hooks/useAgents";

// Helper function to extract pain points
export function extractPainPoints(agents: Agent[]) {
  const completedAgents = agents.filter(a => a.status === "completed" && a.review);

  // Define pain point keywords
  const painPointDefinitions = [
    { 
      text: "Loading times could be improved for better performance", 
      keywords: ["loading", "performance", "slow", "speed"] 
    },
    { 
      text: "Some sections feel cluttered and overwhelming", 
      keywords: ["cluttered", "overwhelming", "crammed", "too much"] 
    },
    { 
      text: "Call-to-action buttons need to be more prominent", 
      keywords: ["call-to-action", "cta", "buttons", "sign up", "action"] 
    },
    { 
      text: "Mobile responsiveness needs refinement", 
      keywords: ["mobile", "responsive", "phone", "smaller screens"] 
    },
    { 
      text: "Navigation structure could be more intuitive", 
      keywords: ["navigation", "menu", "find", "structure"] 
    }
  ];

  // Match reviews to pain points
  const painPoints = painPointDefinitions.map(def => {
    const matchingReviews = completedAgents.filter(agent => 
      def.keywords.some(keyword => agent.review?.toLowerCase().includes(keyword))
    ).map(agent => ({
      agent,
      review: agent.review!
    }));

    return {
      text: def.text,
      mentions: matchingReviews.length,
      reviews: matchingReviews
    };
  }).filter(point => point.mentions > 0)
    .sort((a, b) => b.mentions - a.mentions); // Sort by count descending

  const maxMentions = Math.max(...painPoints.map(p => p.mentions), 1);
  
  return painPoints.map(point => ({
    ...point,
    percentage: (point.mentions / maxMentions) * 100
  }));
}

// Helper function to extract liked features
export function extractLikedFeatures(agents: Agent[]) {
  const completedAgents = agents.filter(a => a.status === "completed" && a.review);

  // Define liked feature keywords
  const featureDefinitions = [
    { 
      text: "Clean and modern design that inspires confidence", 
      keywords: ["clean", "modern", "design", "confidence", "minimalist"] 
    },
    { 
      text: "Clear value proposition is immediately apparent", 
      keywords: ["value proposition", "clear", "immediately", "apparent", "understood"] 
    },
    { 
      text: "Excellent use of whitespace and typography", 
      keywords: ["whitespace", "typography", "readability", "breathes"] 
    },
    { 
      text: "Strong visual hierarchy makes content easy to scan", 
      keywords: ["visual hierarchy", "hierarchy", "scan", "eye flows", "structured"] 
    },
    { 
      text: "Professional brand identity and consistent messaging", 
      keywords: ["brand", "professional", "identity", "consistent", "cohesive"] 
    }
  ];

  // Match reviews to liked features
  const features = featureDefinitions.map(def => {
    const matchingReviews = completedAgents.filter(agent => 
      def.keywords.some(keyword => agent.review?.toLowerCase().includes(keyword))
    ).map(agent => ({
      agent,
      review: agent.review!
    }));

    return {
      text: def.text,
      mentions: matchingReviews.length,
      reviews: matchingReviews
    };
  }).filter(feature => feature.mentions > 0)
    .sort((a, b) => b.mentions - a.mentions); // Sort by count descending

  const maxMentions = Math.max(...features.map(f => f.mentions), 1);
  
  return features.map(feature => ({
    ...feature,
    percentage: (feature.mentions / maxMentions) * 100
  }));
}