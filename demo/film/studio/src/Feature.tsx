import React from "react";
import { AbsoluteFill, interpolate, OffthreadVideo, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { DISPLAY, MONO } from "./brand";
import features from "./data/features.json";

/** One feature, side by side: the real Hermes session (its own colours) and the real phone, step by step. */
type F = (typeof features.features)[number];
const GOLD = "#FFD700";
const BG = "#08080a";
const W_TERM = 780;
const H_TERM = Math.round((W_TERM * 1314) / 1944);
const H_PHONE = H_TERM;
const W_PHONE = Math.round((H_PHONE * 720) / 1600);
const TOP = 132;

export const featureById = (id: string): F => features.features.find((f) => f.id === id) ?? features.features[0];

const Steps: React.FC<{ f: F }> = ({ f }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const active = f.steps.reduce((acc, s, i) => (t >= s.from ? i : acc), 0);
  return (
    <div style={{ position: "absolute", left: 40, right: 40, top: 76, display: "flex", alignItems: "center", gap: 10 }}>
      {f.steps.map((s, i) => {
        const on = i === active;
        const done = i < active;
        const p = interpolate(t, [s.from, s.from + 0.25], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
        return (
          <React.Fragment key={i}>
            {i > 0 ? <div style={{ width: 18, height: 2, background: done || on ? GOLD : "#2b2b33", opacity: 0.8 }} /> : null}
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
                padding: "7px 13px 7px 8px",
                borderRadius: 999,
                background: on ? GOLD : "transparent",
                border: `1.5px solid ${on || done ? GOLD : "#2b2b33"}`,
                color: on ? "#111" : done ? GOLD : "#6b6f7b",
                fontFamily: DISPLAY,
                fontWeight: 700,
                fontSize: 17,
                whiteSpace: "nowrap",
                transform: on ? `scale(${1 + 0.04 * (1 - p)})` : undefined,
              }}
            >
              <span
                style={{
                  width: 22,
                  height: 22,
                  borderRadius: 11,
                  display: "grid",
                  placeItems: "center",
                  fontFamily: MONO,
                  fontSize: 12,
                  background: on ? "#111" : "transparent",
                  color: on ? GOLD : "inherit",
                  border: on ? "none" : "1.5px solid currentColor",
                }}
              >
                {done ? "✓" : i + 1}
              </span>
              {s.label}
            </div>
          </React.Fragment>
        );
      })}
    </div>
  );
};

const Blur: React.FC<{ boxes: number[][] }> = ({ boxes }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const k = H_PHONE / 1600;
  return (
    <>
      {boxes
        .filter(([, , , , from = 0, to = 1e6]) => t >= from && t < to)
        .map(([x, y, w, h], i) => (
          <div key={i} style={{ position: "absolute", left: x * k, top: y * k, width: w * k, height: h * k, borderRadius: 8,
            backdropFilter: "blur(10px)", background: "rgba(20,22,40,.35)" }} />
        ))}
    </>
  );
};

/** Zoom onto the answer once it is on screen, keeping the left edge (text is left-aligned). */
const Zoomed: React.FC<{ f: F; children: React.ReactNode }> = ({ f, children }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const z = (f as { zoom?: { row: number | null; rows: number; from: number } }).zoom;
  if (!z || z.row === null) return <>{children}</>;
  const k = H_TERM / 1314;
  const rowY = (28 + (z.row - (z.rows - 1) / 2) * 37 + 18) * k;
  const p = interpolate(frame / fps, [z.from, z.from + 0.6], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp",
    easing: (x) => 1 - Math.pow(1 - x, 3) });
  const s = 1 + 0.75 * p;
  const want = (H_TERM / 2 - rowY) * p;
  const t = Math.max(-(H_TERM - rowY) * (s - 1), Math.min(rowY * (s - 1), want));
  return <div style={{ transformOrigin: `0px ${rowY}px`, transform: `translateY(${t}px) scale(${s})` }}>{children}</div>;
};

/** Silent clips can't play the phone's voice: show its exact words while it speaks. */
const Said: React.FC<{ f: F }> = ({ f }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const sp = (f as { speech?: { at: number; dur: number; text: string } | null }).speech;
  if (!sp) return null;
  const t = frame / fps;
  const o = interpolate(t, [sp.at, sp.at + 0.3, sp.at + sp.dur + 1.2, sp.at + sp.dur + 1.6], [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <div style={{ position: "absolute", left: 380, top: TOP + 300, width: 560, padding: "18px 22px", borderRadius: 18,
      background: GOLD, color: "#111", opacity: o, translate: `0 ${(1 - o) * 16}px`, boxShadow: "0 24px 70px rgba(0,0,0,.55)" }}>
      <div style={{ fontFamily: MONO, fontSize: 13, letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 6 }}>
        🔊 The phone says, out loud
      </div>
      <div style={{ fontFamily: DISPLAY, fontWeight: 800, fontSize: 28, lineHeight: 1.15 }}>“{sp.text}”</div>
    </div>
  );
};

export const Feature: React.FC<{ id: string }> = ({ id }) => {
  const f = featureById(id);
  const termLeft = f.phone ? 40 : (1280 - W_TERM) / 2;
  return (
    <AbsoluteFill style={{ background: BG }}>
      <div style={{ position: "absolute", left: 40, right: 40, top: 22, display: "flex", alignItems: "center", gap: 14 }}>
        <span style={{ fontFamily: MONO, fontSize: 13, letterSpacing: "0.1em", color: "#8a8f9c", textTransform: "uppercase" }}>
          Phone Senses · Hermes Agent
        </span>
        <span style={{ fontFamily: DISPLAY, fontWeight: 800, fontStretch: "108%", fontSize: 26, color: "#f1f1ee" }}>{f.title}</span>
        <span style={{ flex: 1 }} />
        <span
          style={{
            fontFamily: MONO,
            fontSize: 12,
            letterSpacing: "0.08em",
            padding: "6px 10px",
            borderRadius: 6,
            color: f.real ? "#9ff0c8" : "#ffb08a",
            border: `1px solid ${f.real ? "rgba(124,242,177,.45)" : "rgba(255,138,138,.45)"}`,
          }}
        >
          {f.real ? f.tag : `${f.tag} · FIXTURES`}
        </span>
      </div>
      <Steps f={f} />
      {/* the terminal: plain, like the author's own (kitty, black) */}
      <div style={{ position: "absolute", left: termLeft, top: TOP, width: W_TERM, borderRadius: 10, overflow: "hidden",
        border: "1px solid #26262c", boxShadow: "0 20px 60px rgba(0,0,0,.6)" }}>
        <div style={{ height: 26, background: "#18181c", display: "flex", alignItems: "center", gap: 7, padding: "0 10px" }}>
          {["#ff5f56", "#ffbd2e", "#27c93f"].map((c) => <div key={c} style={{ width: 10, height: 10, borderRadius: 5, background: c }} />)}
          <span style={{ flex: 1, textAlign: "center", fontFamily: MONO, fontSize: 12, color: "#8a8f9c" }}>hermes chat</span>
        </div>
        <div style={{ position: "relative", width: W_TERM, height: H_TERM, overflow: "hidden" }}>
          <Zoomed f={f}>
            <OffthreadVideo src={staticFile(`features/${f.id}/term.mp4`)} muted style={{ width: W_TERM, height: H_TERM, display: "block" }} />
          </Zoomed>
        </div>
      </div>
      {f.phone ? (
        <div style={{ position: "absolute", left: 40 + W_TERM + 60, top: TOP - 4, width: W_PHONE + 16, height: H_PHONE + 16, padding: 8,
          borderRadius: 34, background: "linear-gradient(160deg,#2a2b33,#0c0c12 60%,#1b1c24)", boxShadow: "0 20px 60px rgba(0,0,0,.6), 0 0 0 1px rgba(255,255,255,.1)" }}>
          <div style={{ position: "relative", width: W_PHONE, height: H_PHONE, borderRadius: 26, overflow: "hidden", background: "#000" }}>
            <OffthreadVideo src={staticFile(`features/${f.id}/phone.mp4`)} muted style={{ width: "100%", height: "100%", objectFit: "cover" }} />
            <Blur boxes={f.blur} />
          </div>
        </div>
      ) : null}
      <Said f={f} />
    </AbsoluteFill>
  );
};
