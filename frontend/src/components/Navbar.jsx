import { Globe } from "lucide-react";

export default function Navbar() {
  return (
    <nav className="relative w-full flex items-center justify-between px-6 py-4 max-w-6xl mx-auto z-50">
      <div className="font-serif font-bold text-xl md:text-2xl text-[#1B2A4A] tracking-tight">
        Sarkari Sahayak
      </div>
      
      <div className="flex items-center space-x-6">
        <a href="#about" className="text-[#1B2A4A]/80 hover:text-[#1B2A4A] text-sm font-medium transition-colors hidden md:block">
          About
        </a>
        <a href="#schemes" className="text-[#1B2A4A]/80 hover:text-[#1B2A4A] text-sm font-medium transition-colors hidden md:block">
          Schemes Directory
        </a>
        
        {/* Language Selector Pill */}
        <button className="flex items-center space-x-2 bg-white border border-[#1B2A4A]/15 hover:border-[#1B2A4A]/30 px-3 py-1.5 rounded-full text-[#1B2A4A] text-sm font-medium shadow-sm transition-all focus:outline-none focus:ring-2 focus:ring-[#E8743B]/50">
          <Globe className="w-4 h-4 text-[#1B2A4A]/70" />
          <span>English / हिन्दी</span>
        </button>
      </div>
    </nav>
  );
}
