"use client";

import { useState, useRef, useCallback } from "react";
import { motion } from "framer-motion";
import { Camera, RefreshCw, Check, Upload } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

interface Props {
  modality: "nail" | "tongue" | "skin" | "eye";
  onCapture: (file: File) => void;
  captured?: boolean;
}

const MODALITY_META = {
  nail: { label: "Nakhun", hint: "Haath ke nakhun seedhe camera mein dikhaein", emoji: "💅" },
  tongue: { label: "Jeebh", hint: "Jeebh nikaalein, achhi roshni mein", emoji: "👅" },
  skin: { label: "Skin", hint: "Problematic area ya chehra dikhaein", emoji: "🤲" },
  eye: { label: "Aankhein", hint: "Lower eyelid thodi neeche kheenchein", emoji: "👁️" },
};

export default function CameraCapture({ modality, onCapture, captured }: Props) {
  const [preview, setPreview] = useState<string | null>(null);
  const [streaming, setStreaming] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const meta = MODALITY_META[modality];

  const startCamera = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "environment", width: 640, height: 480 },
      });
      streamRef.current = stream;
      if (videoRef.current) videoRef.current.srcObject = stream;
      setStreaming(true);
    } catch {
      fileRef.current?.click();
    }
  }, []);

  const capture = useCallback(() => {
    if (!videoRef.current) return;
    const canvas = document.createElement("canvas");
    canvas.width = videoRef.current.videoWidth;
    canvas.height = videoRef.current.videoHeight;
    canvas.getContext("2d")?.drawImage(videoRef.current, 0, 0);
    canvas.toBlob((blob) => {
      if (!blob) return;
      const file = new File([blob], `${modality}_capture.jpg`, { type: "image/jpeg" });
      setPreview(canvas.toDataURL("image/jpeg"));
      onCapture(file);
      streamRef.current?.getTracks().forEach((t) => t.stop());
      setStreaming(false);
    }, "image/jpeg", 0.9);
  }, [modality, onCapture]);

  const handleFileUpload = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const url = URL.createObjectURL(file);
    setPreview(url);
    onCapture(file);
  }, [onCapture]);

  const reset = useCallback(() => {
    setPreview(null);
    streamRef.current?.getTracks().forEach((t) => t.stop());
    setStreaming(false);
  }, []);

  return (
    <div className="flex flex-col items-center gap-3">
      <input ref={fileRef} type="file" accept="image/*" capture="environment"
        onChange={handleFileUpload} className="hidden" />

      <div className="relative w-full aspect-square max-w-[200px] rounded-2xl overflow-hidden bg-muted border-2 border-dashed border-border">
        {preview ? (
          <img src={preview} alt="captured" className="w-full h-full object-cover" />
        ) : streaming ? (
          <video ref={videoRef} autoPlay playsInline muted className="w-full h-full object-cover" />
        ) : (
          <div className="flex flex-col items-center justify-center h-full gap-2 p-4">
            <span className="text-4xl">{meta.emoji}</span>
            <p className="text-xs text-muted-foreground text-center">{meta.hint}</p>
          </div>
        )}

        {captured && !preview && (
          <div className="absolute inset-0 bg-primary/10 flex items-center justify-center">
            <Check className="w-8 h-8 text-primary" />
          </div>
        )}
      </div>

      <div className="flex gap-2">
        {!streaming && !preview && (
          <Button size="sm" variant="outline" onClick={startCamera}>
            <Camera className="w-3.5 h-3.5 mr-1.5" /> Photo Lo
          </Button>
        )}
        {!streaming && !preview && (
          <Button size="sm" variant="ghost" onClick={() => fileRef.current?.click()}>
            <Upload className="w-3.5 h-3.5 mr-1.5" /> Upload
          </Button>
        )}
        {streaming && (
          <Button size="sm" onClick={capture} className="bg-primary">
            <Camera className="w-3.5 h-3.5 mr-1.5" /> Capture
          </Button>
        )}
        {preview && (
          <Button size="sm" variant="outline" onClick={reset}>
            <RefreshCw className="w-3.5 h-3.5 mr-1.5" /> Dobara
          </Button>
        )}
      </div>

      <div className="flex items-center gap-1.5">
        <Badge variant={preview ? "default" : "secondary"} className="text-xs">
          {meta.label}
        </Badge>
        {preview && <Check className="w-3 h-3 text-primary" />}
      </div>
    </div>
  );
}
