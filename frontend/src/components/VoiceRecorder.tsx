"use client";

import { useState, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Mic, MicOff, Square, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";

interface Props {
  onTranscript: (text: string) => void;
  onAudioBlob?: (blob: Blob) => void;
  placeholder?: string;
}

type State = "idle" | "recording" | "processing";

export default function VoiceRecorder({ onTranscript, onAudioBlob, placeholder }: Props) {
  const [state, setState] = useState<State>("idle");
  const [volume, setVolume] = useState(0);
  const mediaRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animFrameRef = useRef<number>(0);

  const stopRecording = useCallback(() => {
    if (mediaRef.current && mediaRef.current.state !== "inactive") {
      mediaRef.current.stop();
    }
    if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    setVolume(0);
    setState("processing");
  }, []);

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const ctx = new AudioContext();
      const source = ctx.createMediaStreamSource(stream);
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 256;
      source.connect(analyser);
      analyserRef.current = analyser;

      const getVolume = () => {
        const buf = new Uint8Array(analyser.frequencyBinCount);
        analyser.getByteFrequencyData(buf);
        const avg = buf.reduce((a, b) => a + b, 0) / buf.length;
        setVolume(avg / 128);
        animFrameRef.current = requestAnimationFrame(getVolume);
      };
      getVolume();

      chunksRef.current = [];
      const mr = new MediaRecorder(stream, { mimeType: "audio/webm" });
      mr.ondataavailable = (e) => { if (e.data.size > 0) chunksRef.current.push(e.data); };
      mr.onstop = async () => {
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        onAudioBlob?.(blob);
        stream.getTracks().forEach((t) => t.stop());
        ctx.close();

        // Browser-side Web Speech API transcription (fallback)
        if ("webkitSpeechRecognition" in window || "SpeechRecognition" in window) {
          const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
          const recognition = new SR();
          recognition.lang = "hi-IN";
          recognition.interimResults = false;
          recognition.onresult = (event: any) => {
            const text = event.results[0][0].transcript;
            onTranscript(text);
            setState("idle");
          };
          recognition.onerror = () => setState("idle");
          recognition.start();
        } else {
          setState("idle");
        }
      };

      mediaRef.current = mr;
      mr.start(100);
      setState("recording");
    } catch {
      setState("idle");
      alert("Microphone access needed. Please allow mic permission.");
    }
  }, [onTranscript, onAudioBlob]);

  return (
    <div className="flex flex-col items-center gap-4">
      <div className="relative">
        {/* Pulse rings when recording */}
        <AnimatePresence>
          {state === "recording" && (
            <>
              {[1, 2, 3].map((ring) => (
                <motion.div
                  key={ring}
                  className="absolute inset-0 rounded-full border-2 border-primary/40"
                  initial={{ scale: 1, opacity: 0.6 }}
                  animate={{ scale: 1 + ring * 0.35 + volume * 0.3, opacity: 0 }}
                  transition={{ duration: 1.2, repeat: Infinity, delay: ring * 0.25, ease: "easeOut" }}
                />
              ))}
            </>
          )}
        </AnimatePresence>

        <Button
          onClick={state === "idle" ? startRecording : stopRecording}
          disabled={state === "processing"}
          size="lg"
          className={`relative w-20 h-20 rounded-full transition-all ${
            state === "recording"
              ? "bg-red-500 hover:bg-red-600 shadow-lg shadow-red-500/30"
              : "bg-primary hover:bg-primary/90 glow-green"
          }`}
        >
          {state === "idle" && <Mic className="w-7 h-7" />}
          {state === "recording" && <Square className="w-7 h-7 fill-current" />}
          {state === "processing" && <Loader2 className="w-7 h-7 animate-spin" />}
        </Button>
      </div>

      <p className="text-sm text-muted-foreground text-center">
        {state === "idle" && (placeholder || "Mic dabao aur bolna shuru karo")}
        {state === "recording" && "🔴 Recording... band karne ke liye dabao"}
        {state === "processing" && "Processing aawaz..."}
      </p>
    </div>
  );
}
