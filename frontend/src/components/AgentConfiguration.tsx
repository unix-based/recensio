import { useState, useEffect } from "react";
import { Label } from "./ui/label";
import { Input } from "./ui/input";
import { Button } from "./ui/button";
import { Slider } from "./ui/slider";
import { ChevronDown, ChevronUp } from "lucide-react";
import { motion, AnimatePresence } from "motion/react";
import { EmojiCarousel } from "./EmojiCarousel";

interface AgentFilters {
  ageRange: [number, number];
  gender: string;
  occupation: string;
  lifeViews: string;
  innovationAttitude: string;
  riskTolerance: number;
  gullibility: number;
}

interface AgentConfigurationProps {
  websiteUrl: string;
  mode: "random" | "custom" | "auto";
  onGenerate: (filters: AgentFilters, mode: string) => void;
  onModeChange: (mode: "random" | "custom" | "auto") => void;
}

export function AgentConfiguration({ websiteUrl, mode, onGenerate, onModeChange }: AgentConfigurationProps) {
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [filters, setFilters] = useState<AgentFilters>({
    ageRange: [18, 65],
    gender: "",
    occupation: "",
    lifeViews: "",
    innovationAttitude: "",
    riskTolerance: 5,
    gullibility: 5,
  });
  const [isGenerating, setIsGenerating] = useState(false);

  const updateFilter = <K extends keyof AgentFilters>(key: K, value: AgentFilters[K]) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const handleAutoGenerate = async () => {
    setIsGenerating(true);
    
    try {
      const response = await fetch('http://localhost:8000/api/target-audience/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          website_url: websiteUrl
        })
      });

      if (!response.ok) {
        throw new Error('Failed to generate target audience');
      }

      const result = await response.json();
      
      if (result.success && result.data) {
        console.log('✅ Auto mode: Successfully generated target audience from AI analysis');
        const autoFilters: AgentFilters = {
          ageRange: result.data.ageRange,
          gender: result.data.gender,
          occupation: result.data.occupation,
          lifeViews: result.data.lifeViews,
          innovationAttitude: result.data.innovationAttitude,
          riskTolerance: result.data.riskTolerance,
          gullibility: result.data.gullibility,
        };
        
        // Set the filters and switch to Custom mode to show generated values
        setFilters(autoFilters);
        onModeChange("custom");
      } else {
        console.warn('⚠️ Auto mode: AI analysis failed, using fallback data');
        console.error('Failed to generate target audience:', result);
        // Fallback to default filters
        const defaultFilters: AgentFilters = {
          ageRange: [25, 45],
          gender: "",
          occupation: "Tech professionals, entrepreneurs",
          lifeViews: "progressive",
          innovationAttitude: "moderate",
          riskTolerance: 6,
          gullibility: 3,
        };
        setFilters(defaultFilters);
        onModeChange("custom");
      }
    } catch (error) {
      console.error('❌ Auto mode: Network or server error:', error);
      console.warn('⚠️ Auto mode: Falling back to default target audience');
      // Fallback to default filters
      const defaultFilters: AgentFilters = {
        ageRange: [25, 45],
        gender: "",
        occupation: "Tech professionals, entrepreneurs",
        lifeViews: "progressive", 
        innovationAttitude: "moderate",
        riskTolerance: 6,
        gullibility: 3,
      };
      setFilters(defaultFilters);
      onModeChange("custom");
    } finally {
      setIsGenerating(false);
    }
  };

  const handleGenerate = () => {
    onGenerate(filters, mode);
  };

  return (
    <>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-xl mx-auto"
      >

        <div className="relative">
          <AnimatePresence mode="wait">
          {/* Random Mode */}
          {mode === "random" && (
            <motion.div
              key="random"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="text-center"
            >
              <h2 className="text-6xl text-gray-900 mt-4 mb-8">
                Select Your Audience
              </h2>
              <div className="mt-8">
                <EmojiCarousel />
              </div>
              <div className="mt-6">
                <Button 
                  onClick={handleGenerate}
                  className="bg-gray-900 hover:bg-gray-800 text-white px-8 py-2 h-auto"
                >
                  Generate
                </Button>
              </div>
              <p className="text-gray-500 text-xs mt-6">
                Generate 30 AI agents with random characteristics
              </p>
            </motion.div>
          )}

          {/* Custom Mode */}
          {mode === "custom" && (
            <motion.div
              key="custom"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="space-y-4"
            >
              {/* Age Range */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label className="text-gray-600 text-xs">Age</Label>
                  <span className="text-xs text-gray-400">
                    {filters.ageRange[0]}–{filters.ageRange[1]}
                  </span>
                </div>
                <Slider
                  min={18}
                  max={80}
                  step={1}
                  value={filters.ageRange}
                  onValueChange={(value) => updateFilter("ageRange", value as [number, number])}
                />
              </div>

              {/* Gender */}
              <div className="space-y-2">
                <Label className="text-gray-600 text-xs">Gender</Label>
                <div className="inline-flex rounded-lg border border-gray-200 bg-white p-0.5">
                  <button
                    type="button"
                    onClick={() => updateFilter("gender", filters.gender === "male" ? "" : "male")}
                    className={`px-3 py-1.5 text-xs rounded-md transition-all ${
                      filters.gender === "male"
                        ? "bg-gray-900 text-white"
                        : "text-gray-600 hover:text-gray-900"
                    }`}
                  >
                    Male
                  </button>
                  <button
                    type="button"
                    onClick={() => updateFilter("gender", filters.gender === "female" ? "" : "female")}
                    className={`px-3 py-1.5 text-xs rounded-md transition-all ${
                      filters.gender === "female"
                        ? "bg-gray-900 text-white"
                        : "text-gray-600 hover:text-gray-900"
                    }`}
                  >
                    Female
                  </button>
                </div>
              </div>

              {/* Occupation */}
              <div className="space-y-2">
                <Label htmlFor="occupation" className="text-gray-600 text-xs">Occupation</Label>
                <Input
                  id="occupation"
                  placeholder="Developers, Designers, Entrepreneurs..."
                  value={filters.occupation}
                  onChange={(e) => updateFilter("occupation", e.target.value)}
                  className="border-gray-200 focus:border-gray-400 h-9 text-xs"
                />
              </div>

              {/* Life Views */}
              <div className="space-y-2">
                <Label className="text-gray-600 text-xs">Life Views</Label>
                <div className="inline-flex rounded-lg border border-gray-200 bg-white p-0.5">
                  <button
                    type="button"
                    onClick={() => updateFilter("lifeViews", filters.lifeViews === "progressive" ? "" : "progressive")}
                    className={`px-3 py-1.5 text-xs rounded-md transition-all ${
                      filters.lifeViews === "progressive"
                        ? "bg-gray-900 text-white"
                        : "text-gray-600 hover:text-gray-900"
                    }`}
                  >
                    Progressive
                  </button>
                  <button
                    type="button"
                    onClick={() => updateFilter("lifeViews", filters.lifeViews === "moderate" ? "" : "moderate")}
                    className={`px-3 py-1.5 text-xs rounded-md transition-all ${
                      filters.lifeViews === "moderate"
                        ? "bg-gray-900 text-white"
                        : "text-gray-600 hover:text-gray-900"
                    }`}
                  >
                    Moderate
                  </button>
                  <button
                    type="button"
                    onClick={() => updateFilter("lifeViews", filters.lifeViews === "conservative" ? "" : "conservative")}
                    className={`px-3 py-1.5 text-xs rounded-md transition-all ${
                      filters.lifeViews === "conservative"
                        ? "bg-gray-900 text-white"
                        : "text-gray-600 hover:text-gray-900"
                    }`}
                  >
                    Conservative
                  </button>
                </div>
              </div>

              {/* Innovation */}
              <div className="space-y-2">
                <Label className="text-gray-600 text-xs">Innovation</Label>
                <div className="inline-flex rounded-lg border border-gray-200 bg-white p-0.5">
                  <button
                    type="button"
                    onClick={() => updateFilter("innovationAttitude", filters.innovationAttitude === "conservative" ? "" : "conservative")}
                    className={`px-3 py-1.5 text-xs rounded-md transition-all ${
                      filters.innovationAttitude === "conservative"
                        ? "bg-gray-900 text-white"
                        : "text-gray-600 hover:text-gray-900"
                    }`}
                  >
                    Conservative
                  </button>
                  <button
                    type="button"
                    onClick={() => updateFilter("innovationAttitude", filters.innovationAttitude === "moderate" ? "" : "moderate")}
                    className={`px-3 py-1.5 text-xs rounded-md transition-all ${
                      filters.innovationAttitude === "moderate"
                        ? "bg-gray-900 text-white"
                        : "text-gray-600 hover:text-gray-900"
                    }`}
                  >
                    Moderate
                  </button>
                  <button
                    type="button"
                    onClick={() => updateFilter("innovationAttitude", filters.innovationAttitude === "innovator" ? "" : "innovator")}
                    className={`px-3 py-1.5 text-xs rounded-md transition-all ${
                      filters.innovationAttitude === "innovator"
                        ? "bg-gray-900 text-white"
                        : "text-gray-600 hover:text-gray-900"
                    }`}
                  >
                    Innovator
                  </button>
                </div>
              </div>

              {/* Advanced toggle */}
              <button
                type="button"
                onClick={() => setShowAdvanced(!showAdvanced)}
                className="flex items-center gap-1.5 text-xs text-gray-400 hover:text-gray-600 transition-colors mx-auto"
              >
                {showAdvanced ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                Advanced
              </button>

              {/* Advanced Parameters */}
              <AnimatePresence>
                {showAdvanced && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    exit={{ opacity: 0, height: 0 }}
                    className="space-y-4 overflow-hidden"
                  >
                    {/* Risk Tolerance */}
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <Label className="text-gray-600 text-xs">Risk Tolerance</Label>
                        <span className="text-xs text-gray-400">{filters.riskTolerance}</span>
                      </div>
                      <Slider
                        min={1}
                        max={10}
                        step={1}
                        value={[filters.riskTolerance]}
                        onValueChange={(value) => updateFilter("riskTolerance", value[0])}
                        className="[&_.slider-range]:bg-gradient-to-r [&_.slider-range]:from-amber-400 [&_.slider-range]:to-amber-500"
                      />
                    </div>

                    {/* Gullibility */}
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <Label className="text-gray-600 text-xs">Gullibility</Label>
                        <span className="text-xs text-gray-400">{filters.gullibility}</span>
                      </div>
                      <Slider
                        min={1}
                        max={10}
                        step={1}
                        value={[filters.gullibility]}
                        onValueChange={(value) => updateFilter("gullibility", value[0])}
                        className="[&_.slider-range]:bg-gradient-to-r [&_.slider-range]:from-orange-400 [&_.slider-range]:to-orange-500"
                      />
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              <div className="pt-2 text-center">
                <Button 
                  onClick={handleGenerate}
                  className="bg-gray-900 hover:bg-gray-800 text-white px-8 py-2 h-auto"
                >
                  Generate
                </Button>
              </div>
            </motion.div>
          )}

          {/* Auto Mode */}
          {mode === "auto" && (
            <motion.div
              key="auto"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="text-center"
            >
              <h2 className="text-6xl text-gray-900 mt-4 mb-8">
                AI-Generated Audience
              </h2>
              <div className="mt-8">
                <EmojiCarousel />
              </div>
              <div className="mt-6">
                <Button 
                  onClick={handleAutoGenerate}
                  disabled={isGenerating}
                  className="bg-gray-900 hover:bg-gray-800 text-white px-8 py-2 h-auto"
                >
                  {isGenerating ? "Analyzing..." : "Generate"}
                </Button>
              </div>
              <p className="text-gray-500 text-xs mt-6">
                AI will automatically select optimal audience
              </p>
            </motion.div>
          )}
          </AnimatePresence>
        </div>
      </motion.div>
    </>
  );
}
