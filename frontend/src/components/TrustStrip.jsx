import { ShieldCheck, Database, Languages } from "lucide-react";
import { motion } from "motion/react";

export default function TrustStrip() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ delay: 0.4, duration: 0.5 }}
      className="w-full max-w-4xl mx-auto mt-16 px-4"
    >
      <div className="flex flex-col md:flex-row items-center justify-between py-6 border-t border-[#1B2A4A]/10 gap-4 md:gap-0">
        
        {/* Stat & Source */}
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2 text-[#1B2A4A]/70">
            <Database className="w-4 h-4" />
            <span className="text-sm font-medium">450+ Schemes</span>
          </div>
          <div className="w-1 h-1 rounded-full bg-[#1B2A4A]/20" />
          <span className="text-sm text-[#1B2A4A]/60 font-medium">
            Sourced from official portals
          </span>
        </div>

        {/* Govt Badge & Languages */}
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-1.5 text-sm font-medium text-[#138808] bg-[#138808]/10 px-2.5 py-1 rounded-md border border-[#138808]/20">
            <ShieldCheck className="w-4 h-4" />
            <span>Govt. verified data</span>
          </div>
          <div className="w-1 h-1 rounded-full bg-[#1B2A4A]/20 hidden md:block" />
          <div className="hidden md:flex items-center space-x-2 text-[#1B2A4A]/60">
            <Languages className="w-4 h-4" />
            <span className="text-sm font-medium">12+ Languages</span>
          </div>
        </div>

      </div>
    </motion.div>
  );
}
