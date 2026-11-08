import { loadFont } from "@remotion/fonts";
import React from "react";
import {
  AbsoluteFill,
  Easing,
  interpolate,
  random,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

export const C = {
  blue: "#1F2BFF",
  blueText: "#8B93FF",
  ink: "#050507",
  paper: "#F1F1EE",
  mist: "#9AA0B4",
  graphite: "#5B5F6E",
  ok: "#7CF2B1",
  warn: "#FF8A8A",
  chrome: "linear-gradient(180deg,#ffffff 0%,#e4e4e8 47%,#a6a6b0 53%,#d9d9de 100%)",
};

export const DISPLAY = "Archivo";
export const MONO = "Geist Mono";
export const EXPO = Easing.bezier(0.16, 1, 0.3, 1);
export const EASE_IN = Easing.bezier(0.7, 0, 0.84, 0);

export const fontsReady = Promise.all([
  loadFont({ family: DISPLAY, url: staticFile("fonts/Archivo.ttf"), weight: "100 900", stretch: "62% 125%" }),
  loadFont({ family: MONO, url: staticFile("fonts/GeistMono.ttf"), weight: "100 900" }),
]);

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

/** 0→1 entrance progress with the brand expo-out curve. */
export const useEnter = (startFrame: number, durationFrames = 14) => {
  const frame = useCurrentFrame();
  return interpolate(frame, [startFrame, startFrame + durationFrames], [0, 1], { ...clamp, easing: EXPO });
};

/** Grainy ultramarine/ink field with drifting blobs, dashed grid and vignette (the hero look). */
export const Field: React.FC<{ tone?: "ink" | "paper"; intensity?: number; grid?: boolean }> = ({
  tone = "ink",
  intensity = 1,
  grid = true,
}) => {
  const frame = useCurrentFrame();
  const t = frame / 30;
  const bx = 52 + Math.sin(t * 0.21) * 6;
  const by = 54 + Math.cos(t * 0.17) * 5;
  const base = tone === "ink" ? C.ink : C.paper;
  return (
    <AbsoluteFill style={{ backgroundColor: base, overflow: "hidden" }}>
      <AbsoluteFill
        style={{
          inset: "-25%",
          background:
            tone === "ink"
              ? `radial-gradient(34% 30% at ${bx + 6}% ${by - 4}%, rgba(31,43,255,${0.55 * intensity}) 0%, transparent 70%),
                 radial-gradient(28% 26% at ${100 - bx}% ${100 - by}%, rgba(31,43,255,${0.28 * intensity}) 0%, transparent 70%)`
              : `radial-gradient(38% 30% at ${bx}% ${by}%, #050507 0 50%, transparent 100%),
                 radial-gradient(60% 52% at ${bx - 4}% ${by - 4}%, #1F2BFF 0 45%, transparent 75%)`,
          filter: "blur(40px)",
          rotate: `${-16 + Math.sin(t * 0.1) * 4}deg`,
        }}
      />
      <Grain />
      {grid ? <Grid /> : null}
      <AbsoluteFill style={{ background: "radial-gradient(120% 90% at 50% 50%, transparent 60%, rgba(0,0,0,.55) 100%)" }} />
    </AbsoluteFill>
  );
};

export const Grain: React.FC<{ opacity?: number }> = ({ opacity = 0.16 }) => {
  const frame = useCurrentFrame();
  const seed = Math.floor(frame / 2) % 12;
  return (
    <AbsoluteFill style={{ opacity, mixBlendMode: "overlay", pointerEvents: "none" }}>
      <svg width="100%" height="100%">
        <filter id={`grain-${seed}`}>
          <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed={seed} stitchTiles="stitch" />
        </filter>
        <rect width="100%" height="100%" filter={`url(#grain-${seed})`} />
      </svg>
    </AbsoluteFill>
  );
};

export const Grid: React.FC = () => (
  <AbsoluteFill style={{ pointerEvents: "none" }}>
    {[25, 75].map((x) => (
      <div key={`v${x}`} style={{ position: "absolute", top: 0, bottom: 0, left: `${x}%`, borderLeft: "1px dashed rgba(255,255,255,.16)" }} />
    ))}
    {[18, 82].map((y) => (
      <div key={`h${y}`} style={{ position: "absolute", left: 0, right: 0, top: `${y}%`, borderTop: "1px dashed rgba(255,255,255,.12)" }} />
    ))}
  </AbsoluteFill>
);

/** Tiny mono corner label, like the hero. */
export const Label: React.FC<{ children: React.ReactNode; style?: React.CSSProperties; delay?: number }> = ({
  children,
  style,
  delay = 0,
}) => {
  const p = useEnter(delay, 12);
  return (
    <div
      style={{
        position: "absolute",
        fontFamily: MONO,
        fontWeight: 500,
        fontSize: 18,
        letterSpacing: "0.08em",
        textTransform: "uppercase",
        color: "rgba(241,241,238,.82)",
        lineHeight: 1.35,
        opacity: p,
        translate: `0 ${(1 - p) * 10}px`,
        ...style,
      }}
    >
      {children}
    </div>
  );
};

/** Word-by-word headline reveal: mask, rise and blur-to-sharp, on the brand easing. */
export const Kinetic: React.FC<{
  text: string;
  start?: number;
  stagger?: number;
  size?: number;
  accent?: string[];
  chrome?: boolean;
  align?: "left" | "center";
  exitAt?: number;
  maxWidth?: number;
  weight?: number;
}> = ({ text, start = 0, stagger = 3, size = 112, accent = [], chrome = false, align = "center", exitAt, maxWidth = 1500, weight = 800 }) => {
  const frame = useCurrentFrame();
  const words = text.split(" ");
  const exit = exitAt === undefined ? 0 : interpolate(frame, [exitAt, exitAt + 8], [0, 1], { ...clamp, easing: EASE_IN });
  return (
    <div
      style={{
        display: "flex",
        flexWrap: "wrap",
        justifyContent: align === "center" ? "center" : "flex-start",
        gap: `0 ${size * 0.26}px`,
        maxWidth,
        fontFamily: DISPLAY,
        fontWeight: weight,
        fontStretch: "112%",
        fontSize: size,
        lineHeight: 1.02,
        letterSpacing: "-0.035em",
        opacity: 1 - exit,
        translate: `0 ${-exit * 30}px`,
      }}
    >
      {words.map((w, i) => {
        const p = interpolate(frame, [start + i * stagger, start + i * stagger + 14], [0, 1], { ...clamp, easing: EXPO });
        const isAccent = accent.includes(w.replace(/[.,!?]/g, ""));
        return (
          <span key={i} style={{ display: "inline-block", overflow: "hidden", paddingBottom: size * 0.12 }}>
            <span
              style={{
                display: "inline-block",
                translate: `0 ${(1 - p) * size * 0.45}px`,
                filter: `blur(${(1 - p) * 10}px)`,
                opacity: p,
                color: isAccent ? C.blueText : chrome ? "transparent" : C.paper,
                backgroundImage: chrome && !isAccent ? C.chrome : undefined,
                WebkitBackgroundClip: chrome && !isAccent ? "text" : undefined,
                backgroundClip: chrome && !isAccent ? "text" : undefined,
              }}
            >
              {w}
            </span>
          </span>
        );
      })}
    </div>
  );
};

const BLOCKS = [
  [12, 4, 10, 56], [12, 4, 22, 10], [12, 50, 38, 10], [40, 24, 10, 36], [42, 4, 10, 10], [56, 0, 6, 6],
];

/** The block-built phone mark, assembling block by block with springs; the sensing pixel lands last. */
export const Mark: React.FC<{ size?: number; start?: number; fill?: string }> = ({ size = 200, start = 0, fill = "url(#chromeG)" }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return (
    <svg viewBox="0 0 64 64" width={size} height={size} style={{ overflow: "visible" }}>
      <defs>
        <linearGradient id="chromeG" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#fff" />
          <stop offset=".47" stopColor="#e4e4e8" />
          <stop offset=".53" stopColor="#a6a6b0" />
          <stop offset="1" stopColor="#d9d9de" />
        </linearGradient>
      </defs>
      {BLOCKS.map(([x, y, w, h], i) => {
        const s = spring({ frame: frame - start - i * 3, fps, config: { damping: 14, stiffness: 120, mass: 0.6 } });
        const dx = (random(`bx${i}`) - 0.5) * 80;
        const dy = (random(`by${i}`) - 0.5) * 80 - (i === 5 ? 40 : 0);
        return (
          <rect
            key={i}
            x={x}
            y={y}
            width={w}
            height={h}
            fill={i === 5 ? C.blue : fill}
            style={{ translate: `${(1 - s) * dx}px ${(1 - s) * dy}px`, opacity: Math.min(1, s * 1.4) }}
          />
        );
      })}
    </svg>
  );
};

/** Chrome wordmark with a mask wipe. */
export const Wordmark: React.FC<{ size?: number; start?: number }> = ({ size = 150, start = 0 }) => {
  const p = useEnter(start, 22);
  return (
    <div
      style={{
        fontFamily: DISPLAY,
        fontWeight: 800,
        fontStretch: "112%",
        fontSize: size,
        letterSpacing: "-0.035em",
        lineHeight: 0.95,
        backgroundImage: C.chrome,
        WebkitBackgroundClip: "text",
        backgroundClip: "text",
        color: "transparent",
        clipPath: `inset(0 ${(1 - p) * 100}% 0 0)`,
        filter: `blur(${(1 - p) * 6}px)`,
      }}
    >
      Phone Senses
    </div>
  );
};

/** Glass window frame for the real Hermes recording. */
export const GlassWindow: React.FC<{ title: string; width: number; height: number; children: React.ReactNode; style?: React.CSSProperties }> = ({
  title,
  width,
  height,
  children,
  style,
}) => (
  <div
    style={{
      width,
      height,
      borderRadius: 22,
      overflow: "hidden",
      background: "rgba(10,10,16,.72)",
      border: "1px solid rgba(255,255,255,.14)",
      boxShadow: "0 40px 120px rgba(0,0,0,.6), 0 0 0 1px rgba(31,43,255,.18), inset 0 1px 0 rgba(255,255,255,.12)",
      backdropFilter: "blur(18px)",
      display: "flex",
      flexDirection: "column",
      ...style,
    }}
  >
    <div style={{ height: 52, display: "flex", alignItems: "center", gap: 10, padding: "0 22px", borderBottom: "1px dashed rgba(255,255,255,.12)" }}>
      {["#ff5f56", "#ffbd2e", "#27c93f"].map((c) => (
        <div key={c} style={{ width: 13, height: 13, borderRadius: 7, background: c, opacity: 0.85 }} />
      ))}
      <div style={{ flex: 1, textAlign: "center", fontFamily: MONO, fontSize: 17, color: C.mist, letterSpacing: "0.04em" }}>{title}</div>
    </div>
    <div style={{ flex: 1, position: "relative", overflow: "hidden" }}>{children}</div>
  </div>
);

/** Phone mockup for the real scrcpy recording. */
export const PhoneFrame: React.FC<{ height: number; children: React.ReactNode; style?: React.CSSProperties; label?: string }> = ({
  height,
  children,
  style,
  label,
}) => {
  const width = Math.round(height * (720 / 1600)) + 24;
  return (
    <div style={{ position: "relative", ...style }}>
      <div
        style={{
          width,
          height: height + 24,
          borderRadius: 52,
          padding: 12,
          background: "linear-gradient(160deg,#2a2b33,#0c0c12 60%,#1b1c24)",
          boxShadow: "0 40px 120px rgba(0,0,0,.6), 0 0 0 1px rgba(255,255,255,.12), 0 0 80px rgba(31,43,255,.22)",
        }}
      >
        <div style={{ width: "100%", height: "100%", borderRadius: 42, overflow: "hidden", position: "relative", background: "#000" }}>
          {children}
        </div>
      </div>
      {label ? (
        <div style={{ position: "absolute", left: 0, right: 0, top: height + 46, textAlign: "center", fontFamily: MONO, fontSize: 16, color: C.mist, letterSpacing: "0.08em", textTransform: "uppercase" }}>
          {label}
        </div>
      ) : null}
    </div>
  );
};

/** Short brand callout pill with a leader line to a point. */
export const Callout: React.FC<{ text: string; x: number; y: number; start: number; side?: "left" | "right" }> = ({ text, x, y, start, side = "right" }) => {
  const p = useEnter(start, 12);
  const dir = side === "right" ? 1 : -1;
  return (
    <div style={{ position: "absolute", left: x, top: y, pointerEvents: "none" }}>
      <div style={{ position: "absolute", width: 14, height: 14, borderRadius: 7, background: C.blue, boxShadow: `0 0 0 ${6 + p * 6}px rgba(31,43,255,${0.35 * (1 - p) + 0.12})`, translate: "-7px -7px", scale: `${p}` }} />
      <div style={{ position: "absolute", top: -1, left: dir > 0 ? 10 : undefined, right: dir < 0 ? 10 : undefined, height: 2, width: 70 * p, background: C.blue }} />
      <div
        style={{
          position: "absolute",
          top: -26,
          left: dir > 0 ? 86 : undefined,
          right: dir < 0 ? 86 : undefined,
          whiteSpace: "nowrap",
          padding: "12px 20px",
          borderRadius: 14,
          background: "rgba(31,43,255,.92)",
          color: C.paper,
          fontFamily: DISPLAY,
          fontWeight: 700,
          fontSize: 28,
          letterSpacing: "-0.01em",
          boxShadow: "0 18px 50px rgba(31,43,255,.35), inset 0 1px 0 rgba(255,255,255,.35)",
          opacity: p,
          translate: `${(1 - p) * 16 * dir}px 0`,
        }}
      >
        {text}
      </div>
    </div>
  );
};

/** Section counter + title in the corner (mono, like the website labels). */
export const SectionTag: React.FC<{ index: string; title: string }> = ({ index, title }) => (
  <Label style={{ left: 96, top: 72 }}>
    <span style={{ color: C.blueText }}>{index}</span>&nbsp;&nbsp;{title}
  </Label>
);
