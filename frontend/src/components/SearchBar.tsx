import { Input } from "./ui/input";
import { Alert, AlertDescription } from "./ui/alert";
import { Search, Loader2, AlertCircle, HelpCircle } from "lucide-react";
import { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "./ui/tooltip";

type ValidationState = "idle" | "validating" | "error" | "success";

interface SearchBarProps {
  onValidated?: (url: string) => void;
}

export function SearchBar({ onValidated }: SearchBarProps) {
  const [url, setUrl] = useState("");
  const [isFocused, setIsFocused] = useState(false);
  const [validationState, setValidationState] = useState<ValidationState>("idle");

  const validateUrl = async (urlToValidate: string) => {
    try {
      const response = await fetch("http://localhost:8000/api/evaluations/check-link", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ url: urlToValidate }),
      });
      
      if (!response.ok) {
        return false;
      }
      
      const result = await response.json();
      return result.is_valid;
    } catch (error) {
      console.error("URL validation error:", error);
      return false;
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;

    setValidationState("validating");

    try {
      const isValid = await validateUrl(url);
      
      if (isValid) {
        setValidationState("success");
        // Proceed to next step
        if (onValidated) {
          onValidated(url);
        }
      } else {
        setValidationState("error");
        // Auto-dismiss error after 5 seconds
        setTimeout(() => setValidationState("idle"), 5000);
      }
    } catch (error) {
      setValidationState("error");
      setTimeout(() => setValidationState("idle"), 5000);
    }
  };

  const isValidating = validationState === "validating";

  return (
    <div className="w-full max-w-2xl space-y-4">
      <form onSubmit={handleSubmit}>
        <div className="relative group">
          {/* Glow effect on focus */}
          <div className={`absolute -inset-1 bg-gradient-to-r from-blue-400 to-purple-400 rounded-full blur-lg opacity-0 group-hover:opacity-20 transition-opacity duration-500 ${isFocused ? 'opacity-30' : ''} ${isValidating ? 'opacity-40 animate-pulse' : ''}`}></div>
          
          <div className="relative bg-white rounded-full shadow-lg hover:shadow-xl transition-all duration-300">
            {isValidating ? (
              <Loader2 className="absolute left-5 top-1/2 -translate-y-1/2 w-5 h-5 text-blue-500 animate-spin" />
            ) : (
              <Search className={`absolute left-5 top-1/2 -translate-y-1/2 w-5 h-5 transition-colors duration-300 ${isFocused ? 'text-blue-500' : 'text-gray-400'}`} />
            )}
            <Input
              type="text"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              onFocus={() => setIsFocused(true)}
              onBlur={() => setIsFocused(false)}
              disabled={isValidating}
              placeholder="Enter website URL..."
              className="w-full pl-14 pr-6 py-7 text-base border-0 rounded-full focus:ring-2 focus:ring-blue-400/50 transition-all duration-300 disabled:opacity-70 disabled:cursor-not-allowed"
            />
          </div>
        </div>
      </form>

      {/* Error message */}
      <AnimatePresence>
        {validationState === "error" && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.3, ease: "easeOut" }}
          >
            <Alert className="bg-red-50/50 border-red-200/50 backdrop-blur-sm">
              <AlertCircle className="h-4 w-4 text-red-600" />
              <AlertDescription className="text-red-800 flex items-center gap-2">
                <span>Unfortunately, we will not be able to evaluate this project.</span>
                <TooltipProvider>
                  <Tooltip delayDuration={0}>
                    <TooltipTrigger asChild>
                      <button 
                        type="button"
                        className="inline-flex items-center justify-center hover:bg-red-100 rounded-full p-1 transition-colors"
                        aria-label="View possible reasons"
                      >
                        <HelpCircle className="h-4 w-4 text-red-600" />
                      </button>
                    </TooltipTrigger>
                    <TooltipContent 
                      side="bottom" 
                      align="start"
                      className="max-w-xs p-4 bg-white border-red-200 shadow-lg"
                    >
                      <div className="space-y-2">
                        <p className="text-xs text-gray-700 mb-2">Possible reasons:</p>
                        <ul className="space-y-1.5 text-xs text-gray-600">
                          <li className="flex gap-2">
                            <span className="text-red-500 shrink-0">•</span>
                            <span>Site is inaccessible or protected</span>
                          </li>
                          <li className="flex gap-2">
                            <span className="text-red-500 shrink-0">•</span>
                            <span>Site type not supported</span>
                          </li>
                          <li className="flex gap-2">
                            <span className="text-red-500 shrink-0">•</span>
                            <span>Insufficient information available</span>
                          </li>
                        </ul>
                      </div>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </AlertDescription>
            </Alert>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
