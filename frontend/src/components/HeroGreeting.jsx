import { motion } from "motion/react";

export default function HeroGreeting() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20, transition: { duration: 0.3 } }}
      transition={{ duration: 0.6, ease: "easeOut" }}
      className="flex flex-col items-center justify-center text-center space-y-6 pt-12 pb-8"
    >
      <h1 className="text-5xl md:text-6xl lg:text-7xl tracking-tight font-serif leading-[1.1] max-w-4xl mx-auto flex flex-col md:block">
        <span className="font-light text-[#1B2A4A] mr-2">Welcome to</span>
        <span className="font-semibold text-[#1B2A4A]">Sarkari Sahayak</span>
      </h1>
      <p className="text-lg md:text-xl text-[#1B2A4A]/80 font-normal max-w-2xl leading-relaxed px-4 font-sans">
        Your trusted AI assistant for exploring and understanding Indian welfare programs, available in your own language.
      </p>
    </motion.div>
  );
}
