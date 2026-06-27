import { motion } from "motion/react";
import ReactMarkdown from "react-markdown";
import { cn } from "../lib/utils";
import { Landmark, CheckCircle2 } from "lucide-react";

export default function ChatMessage({ message }) {
  const isAi = message.role === "ai";

  return (
    <motion.div
      initial={{ opacity: 0, y: 10, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.4, ease: "easeOut" }}
      className={cn(
        "flex w-full px-4 md:px-0 mb-6",
        isAi ? "justify-start" : "justify-end"
      )}
    >
      <div
        className={cn(
          "flex max-w-[90%] md:max-w-2xl lg:max-w-3xl",
          isAi ? "flex-row" : "flex-row-reverse"
        )}
      >
        {/* Avatar */}
        <div
          className={cn(
            "flex-shrink-0 w-8 h-8 md:w-10 md:h-10 rounded-full flex items-center justify-center mt-1 shadow-sm border",
            isAi 
              ? "bg-white text-[#1B2A4A] mr-3 md:mr-4 border-gray-200" 
              : "bg-[#1B2A4A] text-white ml-3 md:ml-4 border-[#1B2A4A]"
          )}
        >
          {isAi ? <Landmark className="w-4 h-4 md:w-5 md:h-5" /> : <span className="text-xs md:text-sm font-bold tracking-wider">ME</span>}
        </div>

        {/* Message Bubble Container */}
        <div className="flex flex-col items-start max-w-full">
          <div
            className={cn(
              "px-5 py-4 md:px-6 md:py-5 rounded-2xl md:rounded-3xl text-[15px] md:text-[17px] leading-relaxed font-sans transition-all",
              isAi
                ? "bg-white text-[#1B2A4A] border border-gray-200 rounded-tl-sm md:rounded-tl-md shadow-[0_8px_30px_rgb(27,42,74,0.06)]"
                : "bg-[#E8743B] text-white rounded-tr-sm md:rounded-tr-md shadow-md"
            )}
          >
            {isAi ? (
              <div className="prose prose-sm md:prose-base max-w-none text-[#1B2A4A] prose-p:leading-relaxed prose-headings:font-medium prose-strong:text-[#1B2A4A] prose-strong:font-semibold prose-a:text-[#E8743B]">
                <ReactMarkdown>{message.content}</ReactMarkdown>
              </div>
            ) : (
              <div>{message.content}</div>
            )}
          </div>
          
          {/* Actionability / CTA Button */}
          {message.cta && (
            <button className="mt-3 ml-2 flex items-center space-x-2 bg-[#E8743B] hover:bg-[#d66530] text-white px-5 py-2.5 rounded-xl text-sm font-medium shadow-sm transition-all focus:outline-none focus:ring-2 focus:ring-[#E8743B]/50">
              <span>{message.cta}</span>
            </button>
          )}

          {/* Credibility / Citation Line */}
          {message.citation && (
            <div className="mt-2 ml-2 flex items-center space-x-1.5 text-xs text-[#1B2A4A]/50 font-medium">
              <CheckCircle2 className="w-3.5 h-3.5 text-[#138808]" />
              <span>{message.citation}</span>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
}

export function TypingIndicator() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex w-full px-4 md:px-0 mb-6 justify-start"
    >
      <div className="flex max-w-[85%] md:max-w-2xl flex-row">
        <div className="flex-shrink-0 w-8 h-8 md:w-10 md:h-10 rounded-full bg-white text-[#1B2A4A] mr-3 md:mr-4 flex items-center justify-center mt-1 shadow-sm border border-gray-200">
          <Landmark className="w-4 h-4 md:w-5 md:h-5" />
        </div>
        <div className="px-5 py-4 md:px-6 md:py-5 rounded-2xl md:rounded-3xl bg-white border border-gray-200 shadow-[0_8px_30px_rgb(27,42,74,0.06)] rounded-tl-sm flex items-center space-x-1.5 h-[56px] md:h-[68px]">
          <motion.div
            className="w-2 h-2 md:w-2.5 md:h-2.5 bg-[#1B2A4A]/40 rounded-full"
            animate={{ y: [0, -6, 0], opacity: [0.5, 1, 0.5] }}
            transition={{ duration: 0.8, repeat: Infinity, ease: "easeInOut", delay: 0 }}
          />
          <motion.div
            className="w-2 h-2 md:w-2.5 md:h-2.5 bg-[#1B2A4A]/40 rounded-full"
            animate={{ y: [0, -6, 0], opacity: [0.5, 1, 0.5] }}
            transition={{ duration: 0.8, repeat: Infinity, ease: "easeInOut", delay: 0.15 }}
          />
          <motion.div
            className="w-2 h-2 md:w-2.5 md:h-2.5 bg-[#1B2A4A]/40 rounded-full"
            animate={{ y: [0, -6, 0], opacity: [0.5, 1, 0.5] }}
            transition={{ duration: 0.8, repeat: Infinity, ease: "easeInOut", delay: 0.3 }}
          />
        </div>
      </div>
    </motion.div>
  );
}
