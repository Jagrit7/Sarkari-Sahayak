import { motion } from "motion/react";

export default function Footer() {
  return (
    <motion.footer
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ delay: 0.5, duration: 0.5 }}
      className="w-full py-8 text-center mt-auto"
    >
      <div className="flex items-center justify-center space-x-6 mb-3">
        <a href="#" className="text-sm font-medium text-[#1B2A4A]/50 hover:text-[#1B2A4A] transition-colors">Privacy Policy</a>
        <a href="#" className="text-sm font-medium text-[#1B2A4A]/50 hover:text-[#1B2A4A] transition-colors">Terms of Service</a>
        <a href="#" className="text-sm font-medium text-[#1B2A4A]/50 hover:text-[#1B2A4A] transition-colors">Accessibility</a>
      </div>
      <p className="text-[#1B2A4A]/40 text-xs md:text-sm font-medium max-w-xl mx-auto">
        Empowering citizens by simplifying access to government welfare schemes.
      </p>
    </motion.footer>
  );
}
