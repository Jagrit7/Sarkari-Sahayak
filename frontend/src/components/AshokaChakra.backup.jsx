import { motion } from "motion/react";

export default function AshokaChakra() {
  return (
    <div className="fixed inset-0 pointer-events-none flex items-center justify-center overflow-hidden z-0 opacity-25">
      <motion.div
        animate={{ rotate: 360 }}
        transition={{ duration: 120, repeat: Infinity, ease: "linear" }}
        className="w-[90vw] h-[90vw] max-w-[800px] max-h-[800px] text-[#000080]"
      >
        <svg viewBox="0 0 100 100" className="w-full h-full fill-current">
          {/* Outer circle */}
          <circle cx="50" cy="50" r="48" fill="none" stroke="currentColor" strokeWidth="2.5" />
          {/* Inner hub */}
          <circle cx="50" cy="50" r="7" fill="currentColor" />
          
          {/* 24 Spokes */}
          {Array.from({ length: 24 }).map((_, i) => (
            <polygon
              key={`spoke-${i}`}
              points="50,50 48.5,12 50,2 51.5,12"
              transform={`rotate(${i * 15} 50 50)`}
            />
          ))}
          
          {/* 24 semicircular borders (dots on the inside rim) */}
          {Array.from({ length: 24 }).map((_, i) => (
            <circle
              key={`dot-${i}`}
              cx="50"
              cy="4"
              r="1.2"
              transform={`rotate(${(i * 15) + 7.5} 50 50)`}
            />
          ))}
        </svg>
      </motion.div>
    </div>
  );
}
