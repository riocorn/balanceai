"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Mic, Square, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";

const BACKEND = "http://localhost:8000";

interface Props {
  onTranscript: (text: string) => void;
  placeholder?: string;
}

type State = "idle" | "recording" | "processing";
type Engine = "whisper" | "webspeech" | "none";

export default function VoiceRecorder({ onTranscript, placeholder }: Props) {
  const [recState,  setRecState]  = useState<State>("idle");
  const [engine,    setEngine]    = useState<Engine>("none");
  const [interim,   setInterim]   = useState("");

  const mediaRef   = useRef<MediaRecorder | null>(null);
  const chunksRef  = useRef<Blob[]>([]);
  const wsRecogRef = useRef<any>(null);

  // On mount: set engine (client-only, SSR disabled via dynamic import)
  useEffect(() => {
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (SR) {
      setEngine("webspeech");
    } else {
      // Try Whisper backend only if Web Speech unavailable
      fetch(`${BACKEND}/health`, { signal: AbortSignal.timeout(1500) })
        .then((r) => { if (r.ok) setEngine("whisper"); })
        .catch(() => setEngine("none"));
    }
  }, []);

  // ── WHISPER PATH (gold standard): record → send blob to backend ──
  const startWhisper = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mr = new MediaRecorder(stream, { mimeType: "audio/webm" });
      chunksRef.current = [];
      mr.ondataavailable = (e) => { if (e.data.size > 0) chunksRef.current.push(e.data); };
      mr.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        setRecState("processing");
        try {
          const blob = new Blob(chunksRef.current, { type: "audio/webm" });
          const form = new FormData();
          form.append("audio", blob, "recording.webm");
          form.append("is_vegetarian", "false");

          const res = await fetch(`${BACKEND}/checkin/voice`, { method: "POST", body: form });
          if (!res.ok) throw new Error("backend error");
          const data = await res.json();
          // backend returns full deficiency result — extract transcribed voice_text if present
          const text = data.transcribed_text || data.voice_text || data.symptoms_text || "";
          if (text) onTranscript(text.trim());
          else {
            // backend processed but didn't return text — fall back to webspeech for caption
            fallbackWebSpeech();
            return;
          }
        } catch {
          // backend unavailable mid-session, fall back
          setEngine("webspeech");
          fallbackWebSpeech();
          return;
        }
        setRecState("idle");
      };
      mediaRef.current = mr;
      mr.start(200);
      setRecState("recording");
    } catch {
      setRecState("idle");
    }
  }, [onTranscript]);

  const stopWhisper = useCallback(() => {
    mediaRef.current?.stop();
  }, []);

  // ── WEB SPEECH PATH (fallback): live browser STT ──
  const startWebSpeech = useCallback(() => {
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SR) return;
    const r = new SR();
    r.lang = "hi-IN";
    r.continuous = true;
    r.interimResults = true;
    r.onstart = () => setRecState("recording");
    r.onend   = () => { setRecState("idle"); setInterim(""); };
    r.onerror = () => { setRecState("idle"); setInterim(""); };
    r.onresult = (e: any) => {
      let final = ""; let inter = "";
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const t = e.results[i][0].transcript;
        e.results[i].isFinal ? (final += t) : (inter += t);
      }
      if (final) onTranscript(final.trim());
      setInterim(inter);
    };
    wsRecogRef.current = r;
    r.start();
  }, [onTranscript]);

  const stopWebSpeech = useCallback(() => {
    setRecState("processing");
    wsRecogRef.current?.stop();
  }, []);

  function fallbackWebSpeech() {
    setRecState("idle");
    setEngine("webspeech");
  }

  // ── Unified start/stop ──
  const handleClick = useCallback(() => {
    if (recState === "idle") {
      if (engine === "whisper")   startWhisper();
      else if (engine === "webspeech") startWebSpeech();
    } else if (recState === "recording") {
      if (engine === "whisper")   stopWhisper();
      else if (engine === "webspeech") stopWebSpeech();
    }
  }, [recState, engine, startWhisper, stopWhisper, startWebSpeech, stopWebSpeech]);

  if (engine === "none") {
    return (
      <div className="text-center text-sm py-4" style={{ color: "rgba(255,255,255,0.4)" }}>
        ⚠️ Voice support nahi mili — Type tab use karo
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center gap-4">
      <div className="relative">
        <AnimatePresence>
          {recState === "recording" && [1, 2, 3].map((ring) => (
            <motion.div
              key={ring}
              className="absolute inset-0 rounded-full"
              style={{ border: "2px solid rgba(0,217,126,0.35)" }}
              initial={{ scale: 1, opacity: 0.6 }}
              animate={{ scale: 1 + ring * 0.4, opacity: 0 }}
              transition={{ duration: 1.4, repeat: Infinity, delay: ring * 0.3, ease: "easeOut" }}
            />
          ))}
        </AnimatePresence>

        <Button
          onClick={handleClick}
          disabled={recState === "processing"}
          size="lg"
          className={`relative w-20 h-20 rounded-full transition-all ${
            recState === "recording"
              ? "bg-red-500 hover:bg-red-600 shadow-lg shadow-red-500/30"
              : "bg-primary hover:bg-primary/90"
          }`}
        >
          {recState === "idle"       && <Mic     className="w-7 h-7" />}
          {recState === "recording"  && <Square  className="w-7 h-7 fill-current" />}
          {recState === "processing" && <Loader2 className="w-7 h-7 animate-spin" />}
        </Button>
      </div>

      <div className="text-center space-y-1">
        <p className="text-sm" style={{ color: "rgba(255,255,255,0.45)" }}>
          {recState === "idle"       && (placeholder || "Mic dabao aur bolna shuru karo")}
          {recState === "recording"  && "🔴 Sun raha hoon... band karne ke liye dabao"}
          {recState === "processing" && "⏳ Transcribing..."}
        </p>
        <p className="text-[10px]" style={{ color: "rgba(255,255,255,0.2)" }}>
          {engine === "whisper" ? "🔬 Whisper AI (Gold Standard)" : engine === "webspeech" ? "🔬 Web Speech API (Gold Standard)" : ""}
        </p>
      </div>

      {interim && (
        <p className="text-sm italic text-center px-4" style={{ color: "rgba(255,255,255,0.35)" }}>
          {interim}
        </p>
      )}
    </div>
  );
}
