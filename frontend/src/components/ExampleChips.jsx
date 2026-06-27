import { motion } from "motion/react";
import { ArrowUpRight } from "lucide-react";

const CHIPS = [
  "PM-Kisan eligibility",
  "Ayushman Bharat card kaise banaye",
  "Awas Yojana subsidy",
];

export default function ExampleChips() {
  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, transition: { duration: 0.2 } }}
      transition={{ delay: 0.2, duration: 0.5 }}
      className="flex flex-wrap items-center justify-center gap-2 md:gap-3 px-4 max-w-3xl mx-auto"
    >
      <span className="text-sm font-medium text-[#1B2A4A]/50 mr-2 hidden md:inline-block">Try asking:</span>
      {CHIPS.map((chip, index) => (
        <button
          key={index}
          className="group flex items-center space-x-1.5 bg-white border border-[#1B2A4A]/10 hover:border-[#E8743B]/40 hover:bg-[#E8743B]/5 px-4 py-2 rounded-full text-sm font-medium text-[#1B2A4A]/70 hover:text-[#E8743B] transition-all shadow-sm focus:outline-none focus:ring-2 focus:ring-[#E8743B]/30"
        >
          <span>{chip}</span>
          <ArrowUpRight className="w-3.5 h-3.5 opacity-50 group-hover:opacity-100 transition-opacity" />
        </button>
      ))}
    </motion.div>
  );
}
