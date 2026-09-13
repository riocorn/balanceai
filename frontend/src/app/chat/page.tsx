"use client";

import { useEffect, useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Leaf } from "lucide-react";
import AppShell from "@/components/app/AppShell";
import { getAllAnalyses, getOrCreateProfile, type AnalysisEntry } from "@/lib/db";
import { generateResponse, getGreeting, type ChatMessage } from "@/lib/chat-engine";

function TypingDots() {
  return (
    <div className="flex items-center gap-1 px-4 py-3">
      {[0, 1, 2].map((i) => (
        <motion.div
          key={i}
          className="w-1.5 h-1.5 rounded-full"
          style={{ background: "rgba(0,217,126,0.6)" }}
          animate={{ scale: [1, 1.4, 1], opacity: [0.5, 1, 0.5] }}
          transition={{ duration: 0.9, delay: i * 0.2, repeat: Infinity }}
        />
      ))}
    </div>
  );
}

function MessageBubble({ msg }: { msg: ChatMessage }) {
  const isUser = msg.role === "user";
  return (
    <motion.div
      initial={{ opacity: 0, y: 8, scale: 0.96 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ type: "spring", stiffness: 380, damping: 28 }}
      className={`flex ${isUser ? "justify-end" : "justify-start"} mb-3`}
    >
      {!isUser && (
        <div className="w-7 h-7 rounded-lg bg-[#00d97e] flex items-center justify-center shrink-0 mr-2 mt-0.5">
          <Leaf className="w-3.5 h-3.5 text-black" />
        </div>
      )}
      <div
        className="max-w-[82%] px-4 py-3 rounded-2xl text-sm leading-relaxed whitespace-pre-line"
        style={{
          background: isUser ? "#00d97e" : "rgba(255,255,255,0.06)",
          color: isUser ? "#000" : "rgba(255,255,255,0.85)",
          borderRadius: isUser ? "18px 18px 4px 18px" : "4px 18px 18px 18px",
          fontWeight: isUser ? 500 : 400,
        }}
      >
        {msg.text}
      </div>
    </motion.div>
  );
}

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [chips, setChips] = useState<string[]>([]);
  const [input, setInput] = useState("");
  const [typing, setTyping] = useState(false);
  const [analysis, setAnalysis] = useState<AnalysisEntry | null>(null);
  const [loading, setLoading] = useState(true);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    Promise.all([getAllAnalyses(), getOrCreateProfile()]).then(([analyses, profile]) => {
      const latest = analyses[0] ?? null;
      setAnalysis(latest);
      const greeting = getGreeting(latest, profile.name);
      const id = Math.random().toString(36).slice(2);
      setMessages([{ id, role: "assistant", text: greeting.text, chips: greeting.chips }]);
      setChips(greeting.chips ?? []);
      setLoading(false);
    });
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, typing]);

  const sendMessage = async (text: string) => {
    if (!text.trim() || typing) return;
    const userMsg: ChatMessage = { id: Math.random().toString(36).slice(2), role: "user", text };
    setMessages((prev) => [...prev, userMsg]);
    setChips([]);
    setInput("");
    setTyping(true);

    const response = await generateResponse(text, analysis);
    const assistantMsg: ChatMessage = {
      id: Math.random().toString(36).slice(2),
      role: "assistant",
      text: response.text,
      chips: response.chips,
    };
    setTyping(false);
    setMessages((prev) => [...prev, assistantMsg]);
    setChips(response.chips ?? []);
  };

  if (loading) {
    return (
      <AppShell>
        <div className="flex items-center justify-center min-h-screen">
          <div className="w-8 h-8 border-2 border-[#00d97e] border-t-transparent rounded-full animate-spin" />
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="flex flex-col h-[calc(100vh-3.5rem)] lg:h-screen max-w-2xl mx-auto">
        {/* Header */}
        <div
          className="flex items-center gap-3 px-5 py-4 border-b shrink-0"
          style={{ borderColor: "rgba(255,255,255,0.06)" }}
        >
          <div className="w-9 h-9 rounded-xl bg-[#00d97e] flex items-center justify-center">
            <Leaf className="w-4.5 h-4.5 text-black" />
          </div>
          <div>
            <p className="text-sm font-bold" style={{ color: "rgba(255,255,255,0.9)" }}>BalanceAI Health Chat</p>
            <div className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-[#00d97e] animate-pulse" />
              <p className="text-[10px]" style={{ color: "rgba(0,217,126,0.7)" }}>Online · AI-powered</p>
            </div>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4 py-5 space-y-1">
          <AnimatePresence initial={false}>
            {messages.map((msg) => (
              <MessageBubble key={msg.id} msg={msg} />
            ))}
          </AnimatePresence>

          {typing && (
            <motion.div
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="flex items-start mb-3"
            >
              <div className="w-7 h-7 rounded-lg bg-[#00d97e] flex items-center justify-center shrink-0 mr-2 mt-0.5">
                <Leaf className="w-3.5 h-3.5 text-black" />
              </div>
              <div
                className="rounded-2xl"
                style={{
                  background: "rgba(255,255,255,0.06)",
                  borderRadius: "4px 18px 18px 18px",
                }}
              >
                <TypingDots />
              </div>
            </motion.div>
          )}

          <div ref={bottomRef} />
        </div>

        {/* Quick chips */}
        <AnimatePresence>
          {chips.length > 0 && !typing && (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 8 }}
              className="px-4 pb-2 flex flex-wrap gap-2"
            >
              {chips.map((c) => (
                <button
                  key={c}
                  onClick={() => sendMessage(c)}
                  className="text-xs px-3 py-1.5 rounded-full font-medium transition-all"
                  style={{
                    background: "rgba(0,217,126,0.08)",
                    border: "1px solid rgba(0,217,126,0.2)",
                    color: "rgba(0,217,126,0.85)",
                  }}
                >
                  {c}
                </button>
              ))}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Input bar */}
        <div
          className="px-4 py-3 border-t shrink-0"
          style={{ borderColor: "rgba(255,255,255,0.06)" }}
        >
          <form
            onSubmit={(e) => { e.preventDefault(); sendMessage(input); }}
            className="flex items-center gap-2"
          >
            <input
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Kuch poochho... (e.g. 'Kyun thakaan hoti hai?')"
              disabled={typing}
              className="flex-1 px-4 py-2.5 rounded-xl text-sm outline-none"
              style={{
                background: "rgba(255,255,255,0.05)",
                border: "1px solid rgba(255,255,255,0.1)",
                color: "rgba(255,255,255,0.85)",
              }}
            />
            <button
              type="submit"
              disabled={!input.trim() || typing}
              className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0 transition-all"
              style={{
                background: input.trim() && !typing ? "#00d97e" : "rgba(255,255,255,0.05)",
                border: input.trim() && !typing ? "none" : "1px solid rgba(255,255,255,0.08)",
              }}
            >
              <Send
                className="w-4 h-4"
                style={{ color: input.trim() && !typing ? "#000" : "rgba(255,255,255,0.2)" }}
              />
            </button>
          </form>
          <p className="text-[9px] mt-1.5 text-center" style={{ color: "rgba(255,255,255,0.18)" }}>
            Ye medical advice nahi hai · Serious symptoms mein doctor se milein
          </p>
        </div>
      </div>
    </AppShell>
  );
}
