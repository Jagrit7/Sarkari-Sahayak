import { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import { Mic, Send, Loader2 } from "lucide-react";
import { cn } from "../lib/utils";

export default function ChatInput({ onSendMessage, isTyping }) {
  const [query, setQuery] = useState("");
  const [isListening, setIsListening] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim() && !isTyping) {
      onSendMessage(query);
      setQuery("");
    }
  };

  const handleMicClick = () => {
    setIsListening(!isListening);
    if (!isListening) {
      setTimeout(() => {
        setIsListening(false);
        setQuery(prev => prev + (prev ? " " : "") + "PM-Kisan eligibility rules");
      }, 2000);
    }
  };

  return (
    <div className="w-full max-w-3xl mx-auto relative px-4 mt-2 mb-6">
      <form
        onSubmit={handleSubmit}
        className={cn(
          "relative flex items-center w-full rounded-2xl transition-all duration-300",
          "bg-white border border-gray-200",
          "shadow-[0_8px_30px_rgb(27,42,74,0.08)]",
          "focus-within:border-[#1B2A4A]/20 focus-within:shadow-[0_8px_30px_rgb(27,42,74,0.12)]",
          isListening && "border-[#E8743B]/40 ring-4 ring-[#E8743B]/10"
        )}
      >
        <div className="pl-4 md:pl-5 pr-2 hidden sm:flex items-center">
          <button type="button" className="flex items-center space-x-1.5 bg-[#FAF8F3] hover:bg-gray-100 border border-gray-200 px-3 py-1.5 rounded-full text-xs font-semibold text-[#1B2A4A] transition-colors focus:outline-none focus:ring-2 focus:ring-[#E8743B]/30">
            <span>हिन्दी</span>
            <span className="text-gray-300">|</span>
            <span className="text-[#E8743B]">EN</span>
          </button>
        </div>
        
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask a question..."
          className="w-full bg-transparent border-none outline-none py-5 md:py-6 pl-4 sm:pl-2 pr-32 text-lg md:text-xl text-[#1B2A4A] placeholder-[#1B2A4A]/40 focus:ring-0 rounded-2xl font-sans"
          disabled={isTyping}
        />
        
        <div className="absolute right-2 md:right-3 flex items-center space-x-2">
          <button
            type="button"
            onClick={handleMicClick}
            className={cn(
              "p-3 rounded-xl text-[#1B2A4A]/50 hover:text-[#1B2A4A] hover:bg-gray-100 transition-all focus:outline-none relative",
              isListening && "text-[#E8743B] bg-[#E8743B]/10 hover:text-[#E8743B] hover:bg-[#E8743B]/20"
            )}
            aria-label="Voice input"
          >
            <Mic className="w-6 h-6 transition-colors" />
            
            <AnimatePresence>
              {isListening && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1.5 }}
                  exit={{ opacity: 0, scale: 0.8 }}
                  transition={{
                    repeat: Infinity,
                    duration: 1.5,
                    ease: "easeOut"
                  }}
                  className="absolute inset-0 rounded-xl bg-[#E8743B]/20 -z-10"
                />
              )}
            </AnimatePresence>
          </button>
          
          <button
            type="submit"
            disabled={!query.trim() || isTyping}
            className="p-3.5 rounded-xl bg-[#E8743B] text-white shadow-md shadow-[#E8743B]/30 hover:bg-[#d66530] hover:shadow-lg hover:shadow-[#E8743B]/40 disabled:opacity-40 disabled:hover:bg-[#E8743B] transition-all focus:outline-none focus:ring-2 focus:ring-[#E8743B]/50 focus:ring-offset-2 focus:ring-offset-white"
            aria-label="Send message"
          >
            {isTyping ? (
              <Loader2 className="w-6 h-6 animate-spin" />
            ) : (
              <Send className="w-6 h-6 ml-0.5" />
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
