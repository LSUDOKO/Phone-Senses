import React from "react";
import { AbsoluteFill, Img, staticFile } from "remotion";
import { C, DISPLAY, Field, Grain, Mark, MONO, PhoneFrame, Wordmark } from "./brand";

/** 1280x720 video thumbnail: lockup + the real scam text on the real phone + the promise. */
export const Thumbnail: React.FC = () => (
  <AbsoluteFill style={{ backgroundColor: C.ink }}>
    <Field intensity={1.1} />
    <div style={{ position: "absolute", left: 64, top: 52, fontFamily: MONO, fontSize: 16, letterSpacing: "0.12em", color: C.mist }}>
      <span style={{ color: C.blueText }}>HERMES AGENT</span>&nbsp;&nbsp;PLUGIN · REAL PHONE DEMO
    </div>
    <div style={{ position: "absolute", left: 64, top: 150, display: "flex", alignItems: "center", gap: 22 }}>
      <Mark size={92} start={-100} />
      <Wordmark size={92} start={-100} />
    </div>
    <div
      style={{
        position: "absolute",
        left: 64,
        top: 272,
        width: 700,
        fontFamily: DISPLAY,
        fontWeight: 800,
        fontStretch: "112%",
        fontSize: 56,
        lineHeight: 1.0,
        letterSpacing: "-0.035em",
        color: C.paper,
      }}
    >
      Your AI agent can finally <span style={{ color: C.blueText }}>see your phone.</span>
    </div>
    <div style={{ position: "absolute", left: 64, top: 420, display: "flex", gap: 12 }}>
      {["Scam texts", "UPI money", "Find my phone", "Asks first"].map((t) => (
        <div
          key={t}
          style={{
            padding: "10px 18px",
            borderRadius: 999,
            border: "1px solid rgba(255,255,255,.18)",
            background: "rgba(255,255,255,.06)",
            boxShadow: "inset 0 1px 0 rgba(255,255,255,.25)",
            fontFamily: DISPLAY,
            fontWeight: 650,
            fontSize: 22,
            color: C.paper,
          }}
        >
          {t}
        </div>
      ))}
    </div>
    <div style={{ position: "absolute", right: 70, top: 46, rotate: "4deg" }}>
      <PhoneFrame height={600}>
        <Img src={staticFile("thumb/phone.png")} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
      </PhoneFrame>
    </div>
    <div
      style={{
        position: "absolute",
        right: 200,
        top: 420,
        padding: "14px 22px",
        borderRadius: 16,
        background: C.blue,
        color: C.paper,
        fontFamily: DISPLAY,
        fontWeight: 800,
        fontSize: 30,
        boxShadow: "0 20px 60px rgba(31,43,255,.5), inset 0 1px 0 rgba(255,255,255,.35)",
        rotate: "-3deg",
      }}
    >
      ⚠ Scam, score 85/100
    </div>
    <Grain opacity={0.12} />
  </AbsoluteFill>
);
