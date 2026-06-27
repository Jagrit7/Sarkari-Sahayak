import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "motion/react";
import FluidBackground from "./components/FluidBackground";
import Navbar from "./components/Navbar";
import HeroGreeting from "./components/HeroGreeting";
import ChatInput from "./components/ChatInput";
import ExampleChips from "./components/ExampleChips";
import TrustStrip from "./components/TrustStrip";
import ChatMessage, { TypingIndicator } from "./components/ChatMessage";
import Footer from "./components/Footer";

// Backend endpoint (override with VITE_API_URL in a .env file if you ever move the server)
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

// Calls the real FastAPI /chat endpoint. Sends the new message plus the prior turns
// (so follow-ups like "yes, how do I apply?" keep context) and returns { content, citation, cta }.
const fetchFastAPIResponse = async (query, history) => {
  const res = await fetch(`${API_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message: query,
      history: history.map((m) => ({
        role: m.role === "ai" ? "assistant" : "user",
        content: m.content,
      })),
    }),
  });
  if (!res.ok) throw new Error(`Backend returned ${res.status}`);
  return await res.json();
};

export default function App() {
  const [messages, setMessages] = useState([]);
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);

  const hasMessages = messages.length > 0;

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  const handleSendMessage = async (query) => {
    if (!query.trim()) return;

    // Add user message
    const userMessage = { role: "user", content: query };
    setMessages((prev) => [...prev, userMessage]);
    setIsTyping(true);

    // Fetch AI response (pass the existing messages as history — they're the prior turns,
    // since this `messages` value is from before the new user message is appended)
    try {
      const responseData = await fetchFastAPIResponse(query, messages);
      setMessages((prev) => [...prev, { role: "ai", ...responseData }]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        { role: "ai", content: "Sorry, I am having trouble connecting right now." },
      ]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="min-h-screen relative flex flex-col font-sans selection:bg-[#E8743B]/20 selection:text-[#1B2A4A] overflow-hidden">
      
      {/* Restored Flag Background Layer */}
      <FluidBackground />

      {/* Top Navbar */}
      <AnimatePresence>
        {!hasMessages && (
          <motion.div
            className="relative z-20 w-full"
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.4 }}
          >
            <Navbar />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main Content Area */}
      <main className="flex-1 w-full max-w-3xl mx-auto flex flex-col relative z-10 px-4 pb-4 md:pb-8 h-full max-h-screen">
        
        {/* Chat History Area (Bottom anchored) */}
        <AnimatePresence>
          {hasMessages && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.5 }}
              className="flex-1 w-full flex flex-col overflow-y-auto mt-20 md:mt-24 pb-2 hide-scrollbar"
            >
              {/* `mt-auto` pushes content to the bottom so it naturally flows upwards like iMessage */}
              <div className="mt-auto flex flex-col justify-end">
                {messages.map((msg, index) => (
                  <ChatMessage key={index} message={msg} />
                ))}
                {isTyping && <TypingIndicator />}
                <div ref={messagesEndRef} className="h-1" />
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Dynamic Center/Bottom Layout */}
        <motion.div
          layout
          className="w-full shrink-0"
          initial={false}
          animate={
            hasMessages
              ? { y: 0, marginTop: "0px" }
              : { y: 0, marginTop: "15vh" } // Reduced from 45vh to a reasonable offset
          }
          transition={{
            type: "spring",
            stiffness: 70,
            damping: 15,
            mass: 0.8,
          }}
        >
          <AnimatePresence mode="wait">
            {!hasMessages && <HeroGreeting key="greeting" />}
          </AnimatePresence>
          
          <motion.div layout className="w-full">
            <ChatInput onSendMessage={handleSendMessage} isTyping={isTyping} />
          </motion.div>

          <AnimatePresence mode="wait">
            {!hasMessages && <ExampleChips key="chips" />}
          </AnimatePresence>
          
          <AnimatePresence mode="wait">
            {!hasMessages && <TrustStrip key="trust" />}
          </AnimatePresence>
        </motion.div>

      </main>

      {/* Footer Area */}
      <AnimatePresence>
        {!hasMessages && <Footer key="footer" />}
      </AnimatePresence>
      
    </div>
  );
}
