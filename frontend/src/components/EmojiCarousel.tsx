import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "motion/react";

const emojis = [
  "👨‍💻", "👩‍🎨", "🧑‍🚀", "👨‍⚕️", "👩‍🏫", "🧑‍💼",
  "👨‍🔬", "👩‍💻", "🧑‍🎤", "👨‍🎓", "👩‍🔧", "🧑‍🎨",
  "👨‍🚀", "👩‍💼", "🧑‍🔬", "👨‍🎨", "👩‍⚕️", "🧑‍💻",
  "👨‍🏫", "👩‍🎓", "🧑‍⚕️", "👨‍💼", "👩‍🚀", "🧑‍🏫",
  "👨‍🎤", "👩‍🔬", "🧑‍🎓", "👨‍🔧", "👩‍🎤", "🧑‍🔧"
];

export function EmojiCarousel() {
  const [currentIndex, setCurrentIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentIndex((prev) => (prev + 1) % emojis.length);
    }, 2500);

    return () => clearInterval(interval);
  }, []);

  const getVisibleEmojis = () => {
    const prev = (currentIndex - 1 + emojis.length) % emojis.length;
    const current = currentIndex;
    const next = (currentIndex + 1) % emojis.length;
    
    return [
      { emoji: emojis[prev], position: "left" },
      { emoji: emojis[current], position: "center" },
      { emoji: emojis[next], position: "right" },
    ];
  };

  const visible = getVisibleEmojis();

  return (
    <div className="relative h-28 flex items-center justify-center overflow-visible">
      <div className="relative w-full h-full flex items-center justify-center">
        <AnimatePresence mode="popLayout">
          {visible.map((item, index) => (
            <motion.div
              key={`${item.emoji}-${currentIndex}-${index}`}
              initial={{ 
                x: 150,
                opacity: 0,
                scale: 0.6,
              }}
              animate={{ 
                x: index === 0 ? -90 : index === 1 ? 0 : 90,
                opacity: index === 1 ? 1 : 0.3,
                scale: index === 1 ? 1.4 : 0.8,
              }}
              exit={{ 
                x: -150,
                opacity: 0,
                scale: 0.6,
              }}
              transition={{
                duration: 0.9,
                ease: [0.32, 0.72, 0, 1],
              }}
              className="absolute text-6xl emoji-apple"
              style={{
                filter: index === 1 ? 'none' : 'blur(1px)',
              }}
            >
              {item.emoji}
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
}
