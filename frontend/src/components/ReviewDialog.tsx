import { Agent } from "../hooks/useAgents";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "./ui/dialog";
import { ScrollArea } from "./ui/scroll-area";
import { Avatar } from "./ui/avatar";
import { TrendingDown, TrendingUp } from "lucide-react";

interface ReviewDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  selectedItem: {
    type: "pain" | "feature";
    text: string;
    reviews: Array<{ agent: Agent; review: string }>;
  } | null;
}

export function ReviewDialog({ open, onOpenChange, selectedItem }: ReviewDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[80vh] bg-gradient-to-br from-gray-50 to-white">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-3">
            {selectedItem?.type === "pain" ? (
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-orange-100 to-orange-200 flex items-center justify-center">
                <TrendingDown className="w-4 h-4 text-orange-600" />
              </div>
            ) : (
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-teal-100 to-teal-200 flex items-center justify-center">
                <TrendingUp className="w-4 h-4 text-teal-600" />
              </div>
            )}
            <div className="flex-1">
              <div className="text-xs text-gray-500">
                {selectedItem?.type === "pain" ? "Pain Point" : "Liked Feature"}
              </div>
              <div className="text-sm text-gray-900">{selectedItem?.text}</div>
            </div>
          </DialogTitle>
          <DialogDescription className="text-xs">
            {selectedItem?.reviews.length} {selectedItem?.reviews.length === 1 ? 'review mentions' : 'reviews mention'} this {selectedItem?.type === "pain" ? "pain point" : "feature"}
          </DialogDescription>
        </DialogHeader>
        <ScrollArea className="h-[500px] pr-4">
          <div className="space-y-3">
            {selectedItem?.reviews.map((review, index) => (
              <div
                key={index}
                className={`p-3 rounded-lg transition-all ${
                  selectedItem.type === "pain"
                    ? "bg-orange-50/30 hover:bg-orange-50/50"
                    : "bg-teal-50/30 hover:bg-teal-50/50"
                }`}
              >
                <div className="flex items-center gap-2.5 mb-2.5">
                  <div className="w-9 h-9 rounded-full bg-gradient-to-br from-gray-100 to-gray-200 flex items-center justify-center">
                    <span className="text-base">{review.agent.emoji}</span>
                  </div>
                  <div>
                    <div className="text-xs text-gray-900">{review.agent.name}</div>
                    <div className="text-xs text-gray-500">
                      {review.agent.occupation} • {review.agent.age}
                    </div>
                  </div>
                </div>
                <p className="text-xs text-gray-700 leading-relaxed">
                  "{review.review}"
                </p>
                {review.agent.ratings && (
                  <div className="flex gap-3 mt-2.5 pt-2.5 border-t border-gray-200/60">
                    <div className="text-xs">
                      <span className="text-gray-500">Overall:</span>{" "}
                      <span className="text-gray-900 tabular-nums">{review.agent.ratings.overall}</span>
                    </div>
                    <div className="text-xs">
                      <span className="text-gray-500">UX:</span>{" "}
                      <span className="text-gray-900 tabular-nums">{review.agent.ratings.ux}</span>
                    </div>
                    <div className="text-xs">
                      <span className="text-gray-500">Clarity:</span>{" "}
                      <span className="text-gray-900 tabular-nums">{review.agent.ratings.clarity}</span>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </ScrollArea>
      </DialogContent>
    </Dialog>
  );
}