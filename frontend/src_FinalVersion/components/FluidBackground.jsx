import { motion } from "motion/react";

export default function FluidBackground() {
  return (
    <div className="fixed inset-0 z-0 pointer-events-none overflow-hidden bg-[#fafafa]">
      
      {/* ── SAFFRON (TOP) ── */}
      {/* Main Saffron wave - covers top left to center, warps like a flag */}
      <motion.div
        animate={{
          y: [0, 20, -10, 15, 0],
          x: [0, 15, -10, 20, 0],
          scale: [1, 1.05, 0.95, 1.02, 1],
          borderRadius: [
            "40% 60% 55% 45% / 50% 40% 60% 50%",
            "55% 45% 40% 60% / 40% 55% 45% 55%",
            "45% 55% 60% 40% / 55% 45% 50% 50%",
            "50% 50% 45% 55% / 45% 50% 55% 45%",
            "40% 60% 55% 45% / 50% 40% 60% 50%",
          ],
        }}
        transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
        className="absolute -top-[20%] -left-[10%] w-[70vw] h-[60vh] bg-[#F97316] opacity-90 blur-[100px]"
      />
      
      {/* Secondary Saffron wave - dips down on the right side to create the S-curve */}
      <motion.div
        animate={{
          y: [0, -25, 15, -10, 0],
          x: [0, 20, -15, 10, 0],
          scale: [1, 1.1, 0.9, 1.05, 1],
          borderRadius: [
            "50% 50% 40% 60% / 45% 55% 45% 55%",
            "40% 60% 50% 50% / 55% 45% 50% 50%",
            "55% 45% 55% 45% / 45% 55% 45% 55%",
            "45% 55% 45% 55% / 50% 50% 50% 50%",
            "50% 50% 40% 60% / 45% 55% 45% 55%",
          ],
        }}
        transition={{ duration: 5, repeat: Infinity, ease: "easeInOut" }}
        className="absolute -top-[10%] right-[0%] w-[60vw] h-[55vh] bg-[#EA580C] opacity-80 blur-[120px]"
      />

      {/* ── GREEN (BOTTOM) ── */}
      {/* Main Green wave - bottom left, relatively low */}
      <motion.div
        animate={{
          y: [0, -20, 10, -15, 0],
          x: [0, 30, -10, 20, 0],
          scale: [1, 1.05, 0.95, 1.02, 1],
          borderRadius: [
            "45% 55% 50% 50% / 55% 45% 55% 45%",
            "50% 50% 55% 45% / 45% 55% 45% 55%",
            "40% 60% 45% 55% / 55% 45% 50% 50%",
            "55% 45% 50% 50% / 50% 50% 55% 45%",
            "45% 55% 50% 50% / 55% 45% 55% 45%",
          ],
        }}
        transition={{ duration: 7, repeat: Infinity, ease: "easeInOut" }}
        className="absolute -bottom-[20%] -left-[5%] w-[65vw] h-[55vh] bg-[#22C55E] opacity-80 blur-[100px]"
      />

      {/* Secondary Green wave - swoops UP on the right side to complete the S-curve */}
      <motion.div
        animate={{
          y: [0, 30, -15, 20, 0],
          x: [0, -20, 15, -10, 0],
          scale: [1, 1.08, 0.92, 1.06, 1],
          borderRadius: [
            "55% 45% 50% 50% / 50% 50% 50% 50%",
            "45% 55% 45% 55% / 55% 45% 55% 45%",
            "50% 50% 55% 45% / 45% 55% 45% 55%",
            "55% 45% 45% 55% / 50% 50% 50% 50%",
            "55% 45% 50% 50% / 50% 50% 50% 50%",
          ],
        }}
        transition={{ duration: 5.5, repeat: Infinity, ease: "easeInOut" }}
        className="absolute bottom-[0%] right-[-10%] w-[60vw] h-[65vh] bg-[#16A34A] opacity-75 blur-[120px]"
      />

      {/* Clean white center blending layer to ensure the pure white band in the middle */}
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-white/40 to-transparent mix-blend-overlay" />
      <div className="absolute inset-0 bg-white/20 backdrop-blur-[20px]" />
    </div>
  );
}
