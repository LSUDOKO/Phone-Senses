import React from "react";
import { AbsoluteFill, interpolate, random, useCurrentFrame } from "remotion";
import {
  C,
  DISPLAY,
  EASE_IN,
  EXPO,
  Kinetic,
  Mark,
  MONO,
  Wordmark,
} from "../brand";
import {
  clamp,
  FilmField,
  Headline,
  Icon,
  IconName,
  mono,
  Reveal,
  Tag,
  useCues,
  useInOut,
} from "../motion";
import { DESK, DeskLine, LaptopOutline, PhoneOutline } from "../motion/desk";

const ID = "turn";

/** Opens on Problem's last frame: the broken link fuses in ultramarine and light runs along it. */
const Fuse: React.FC<{ fuseAt: number; outAt: number }> = ({
  fuseAt,
  outAt,
}) => {
  const frame = useCurrentFrame();
  const fuse = interpolate(frame, [fuseAt, fuseAt + 12], [0, 1], {
    ...clamp,
    easing: EXPO,
  });
  const sweep = interpolate(frame, [fuseAt + 8, fuseAt + 22], [0, 1], {
    ...clamp,
    easing: EXPO,
  });
  const out = interpolate(frame, [outAt, outAt + 8], [0, 1], {
    ...clamp,
    easing: EASE_IN,
  });
  return (
    <AbsoluteFill style={{ opacity: 1 - out }}>
      <LaptopOutline cursorOn={false} />
      <PhoneOutline glow={fuse * 0.6} />
      <DeskLine
        id="turn"
        draw={1}
        brk={1}
        fuse={fuse}
        sweep={frame >= fuseAt + 8 && frame < fuseAt + 22 ? sweep : -1}
      />
    </AbsoluteFill>
  );
};

/** Notification fragments burst from the phone, snap into a clean grid, turn ultramarine, then collapse into the mark. */
const Order: React.FC<{
  at: number;
  gridAt: number;
  blueAt: number;
  collapseAt: number;
}> = ({ at, gridAt, blueAt, collapseAt }) => {
  const frame = useCurrentFrame();
  const COLS = 9;
  const ROWS = 5;
  const W = 150;
  const H = 40;
  const GX = 18;
  const GY = 18;
  const gw = COLS * W + (COLS - 1) * GX;
  const gh = ROWS * H + (ROWS - 1) * GY;
  const ox = DESK.phone.x + DESK.phone.w / 2;
  const oy = DESK.phone.y + DESK.phone.h / 2;
  const blue = interpolate(frame, [blueAt, blueAt + 10], [0, 1], clamp);
  const col = interpolate(frame, [collapseAt, collapseAt + 12], [0, 1], {
    ...clamp,
    easing: EASE_IN,
  });
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {Array.from({ length: COLS * ROWS }).map((_, i) => {
        const burst = interpolate(
          frame,
          [at + (i % 7), at + (i % 7) + 12],
          [0, 1],
          { ...clamp, easing: EXPO },
        );
        if (burst <= 0 || col >= 1) return null;
        const snap = interpolate(
          frame,
          [gridAt + (i % COLS), gridAt + (i % COLS) + 12],
          [0, 1],
          { ...clamp, easing: EXPO },
        );
        const cx = 960 + (random(`cx${i}`) - 0.5) * 1700;
        const cy = 540 + (random(`cy${i}`) - 0.5) * 900;
        const rot = (random(`cr${i}`) - 0.5) * 50;
        const gx = 960 - gw / 2 + (i % COLS) * (W + GX) + W / 2;
        const gy = 540 - gh / 2 + Math.floor(i / COLS) * (H + GY) + H / 2;
        const x0 = ox + (cx - ox) * burst;
        const y0 = oy + (cy - oy) * burst;
        const x = x0 + (gx - x0) * snap + (450 - gx) * col;
        const y = y0 + (gy - y0) * snap + (540 - gy) * col;
        const b = Math.min(1, blue * 1.4 - (i % COLS) * 0.04);
        const bb = Math.max(0, b);
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: x - W / 2,
              top: y - H / 2,
              width: W,
              height: H,
              borderRadius: 10,
              background: `rgba(${Math.round(120 - 89 * bb)},${Math.round(124 - 81 * bb)},${Math.round(140 + 115 * bb)},${0.3 + 0.55 * bb})`,
              border: `1px solid rgba(255,255,255,${0.12 + 0.1 * bb})`,
              rotate: `${rot * (1 - snap)}deg`,
              scale: `${1 - col * 0.95}`,
              opacity: burst,
              boxShadow:
                bb > 0
                  ? `0 0 ${24 * bb}px rgba(31,43,255,${0.5 * bb})`
                  : undefined,
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};

/** Mark + wordmark lockup that lifts away when the next beat starts. */
const Lockup: React.FC<{ markAt: number; wordAt: number; outAt: number }> = ({
  markAt,
  wordAt,
  outAt,
}) => {
  const frame = useCurrentFrame();
  const out = interpolate(frame, [outAt, outAt + 10], [0, 1], {
    ...clamp,
    easing: EASE_IN,
  });
  const flash = interpolate(
    frame,
    [markAt + 14, markAt + 17, markAt + 30],
    [0, 1, 0],
    clamp,
  );
  return (
    <AbsoluteFill
      style={{
        alignItems: "center",
        justifyContent: "center",
        opacity: 1 - out,
        translate: `0 ${-out * 60}px`,
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 40,
          whiteSpace: "nowrap",
        }}
      >
        <div style={{ position: "relative" }}>
          <Mark size={180} start={markAt} />
          <div
            style={{
              position: "absolute",
              left: 166 - 90,
              top: 8 - 90,
              width: 180,
              height: 180,
              borderRadius: 180,
              background: `radial-gradient(circle, rgba(139,147,255,${flash}) 0%, rgba(31,43,255,${0.5 * flash}) 25%, transparent 65%)`,
            }}
          />
        </div>
        <Wordmark size={136} start={wordAt} />
      </div>
    </AbsoluteFill>
  );
};

/** Hermes -> Phone Senses -> your phone, with six senses lighting up along the way. */
const Senses: React.FC<{ at: number; out: number }> = ({ at, out }) => {
  const frame = useCurrentFrame();
  const { v } = useInOut(at, out, 14, 8);
  const line = interpolate(frame, [at + 6, at + 26], [0, 1], {
    ...clamp,
    easing: EXPO,
  });
  const sweep = ((frame - at - 20) % 40) / 40;
  const nodes: {
    x: number;
    label: string;
    sub: string;
    icon?: IconName;
    mark?: boolean;
  }[] = [
    { x: 420, label: "Hermes", sub: "On his laptop", icon: "grid" },
    { x: 960, label: "Phone Senses", sub: "Hermes plugin", mark: true },
    { x: 1500, label: "His phone", sub: "Android · Termux:API", icon: "call" },
  ];
  const senses: [IconName, string][] = [
    ["bell", "Notifications"],
    ["sms", "SMS"],
    ["rupee", "Money"],
    ["call", "Calls"],
    ["battery", "Battery"],
    ["pin", "Location"],
  ];
  const Y = 560;
  return (
    <AbsoluteFill style={{ opacity: v }}>
      <svg
        width={1920}
        height={1080}
        style={{ position: "absolute", inset: 0 }}
      >
        <line
          x1={420}
          y1={Y}
          x2={420 + 1080 * line}
          y2={Y}
          stroke={C.blue}
          strokeWidth={4}
          style={{ filter: "drop-shadow(0 0 10px rgba(31,43,255,.9))" }}
        />
        {line >= 1 && frame > at + 20 ? (
          <circle
            cx={420 + 1080 * sweep}
            cy={Y}
            r={8}
            fill="#fff"
            style={{
              filter:
                "drop-shadow(0 0 12px #1F2BFF) drop-shadow(0 0 28px #1F2BFF)",
            }}
          />
        ) : null}
      </svg>
      {nodes.map((n, i) => {
        const p = interpolate(frame, [at + i * 6, at + i * 6 + 14], [0, 1], {
          ...clamp,
          easing: EXPO,
        });
        return (
          <div
            key={n.label}
            style={{
              position: "absolute",
              left: n.x - 140,
              top: Y - 70,
              width: 280,
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              opacity: p,
              translate: `0 ${(1 - p) * 30}px`,
            }}
          >
            <div
              style={{
                width: 140,
                height: 140,
                borderRadius: 36,
                background: n.mark
                  ? "rgba(31,43,255,.22)"
                  : "rgba(20,21,30,.92)",
                border: `1px solid ${n.mark ? "rgba(139,147,255,.7)" : "rgba(255,255,255,.16)"}`,
                boxShadow: n.mark
                  ? "0 0 60px rgba(31,43,255,.55)"
                  : "0 20px 60px rgba(0,0,0,.5)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: C.paper,
              }}
            >
              {n.mark ? (
                <Mark size={76} start={-100} />
              ) : (
                <Icon name={n.icon!} size={60} stroke={1.5} />
              )}
            </div>
            <div
              style={{
                fontFamily: DISPLAY,
                fontWeight: 800,
                fontStretch: "112%",
                fontSize: 34,
                color: C.paper,
                marginTop: 22,
                letterSpacing: "-0.02em",
              }}
            >
              {n.label}
            </div>
            <div style={{ ...mono(15), marginTop: 6 }}>{n.sub}</div>
          </div>
        );
      })}
      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          top: 800,
          display: "flex",
          justifyContent: "center",
          gap: 22,
        }}
      >
        {senses.map(([icon, label], i) => {
          const s = at + 34 + i * 6;
          const p = interpolate(frame, [s, s + 10], [0, 1], {
            ...clamp,
            easing: EXPO,
          });
          const lit = interpolate(
            frame,
            [s, s + 4, s + 20],
            [0, 1, 0.35],
            clamp,
          );
          return (
            <div
              key={label}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 10,
                padding: "10px 18px",
                borderRadius: 999,
                background: `rgba(31,43,255,${0.12 + lit * 0.5})`,
                border: "1px solid rgba(139,147,255,.35)",
                color: C.paper,
                opacity: p,
                translate: `0 ${(1 - p) * 16}px`,
              }}
            >
              <Icon name={icon} size={26} />
              <span style={mono(16, { color: C.paper })}>{label}</span>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

/** Screen agents tap pixels (left, dim, struck); Phone Senses asks Android directly (right, ultramarine). */
const NoTapping: React.FC<{ at: number; out: number }> = ({ at, out }) => {
  const frame = useCurrentFrame();
  const { v } = useInOut(at, out, 14, 8);
  const strike = interpolate(frame, [at + 30, at + 40], [0, 1], {
    ...clamp,
    easing: EXPO,
  });
  const tap = (k: number) => {
    const t = (frame - at - k * 9) % 27;
    return t >= 0 && t < 12 ? t / 12 : -1;
  };
  const lines: [string, string][] = [
    ["$ ", "termux-battery-status"],
    ["", '{ "percentage": 64,'],
    ["", '  "status": "CHARGING" }'],
    ["$ ", "termux-sms-list -l 20"],
    ["", "[ 20 messages · read locally ]"],
  ];
  return (
    <AbsoluteFill style={{ opacity: v }}>
      {/* left: screen tapping */}
      <div
        style={{
          position: "absolute",
          left: 400,
          top: 360,
          opacity: 1 - strike * 0.55,
        }}
      >
        <svg width={300} height={560} style={{ overflow: "visible" }}>
          <rect
            x={0}
            y={0}
            width={260}
            height={520}
            rx={40}
            fill="rgba(10,10,16,.6)"
            stroke="rgba(241,241,238,.4)"
            strokeWidth={2}
            strokeDasharray="8 8"
          />
          {[0, 1, 2, 3].map((r) =>
            [0, 1, 2].map((c) => (
              <rect
                key={`${r}${c}`}
                x={36 + c * 68}
                y={70 + r * 80}
                width={50}
                height={50}
                rx={14}
                fill="rgba(241,241,238,.08)"
                stroke="rgba(241,241,238,.18)"
              />
            )),
          )}
          {[0, 1, 2].map((k) => {
            const t = tap(k);
            const pts = [
              [104, 196],
              [176, 276],
              [60, 356],
            ][k];
            return t < 0 ? null : (
              <circle
                key={k}
                cx={pts[0]}
                cy={pts[1]}
                r={10 + t * 34}
                fill="none"
                stroke="rgba(241,241,238,.7)"
                strokeWidth={2}
                opacity={1 - t}
              />
            );
          })}
          <line
            x1={-10}
            y1={530}
            x2={-10 + 280 * strike}
            y2={530 - 540 * strike}
            stroke={C.paper}
            strokeWidth={4}
            strokeLinecap="round"
          />
        </svg>
        <div
          style={{
            ...mono(16),
            marginTop: 22,
            marginLeft: -70,
            width: 400,
            textAlign: "center",
          }}
        >
          Screen agents · tap pixels
        </div>
      </div>
      {/* right: talks to Android directly */}
      <div style={{ position: "absolute", left: 860, top: 420 }}>
        <Reveal at={at + 10} rise={24}>
          <div
            style={{
              width: 800,
              borderRadius: 22,
              background: "rgba(10,10,18,.82)",
              border: "1px solid rgba(139,147,255,.45)",
              boxShadow:
                "0 0 0 1px rgba(31,43,255,.25), 0 30px 90px rgba(0,0,0,.6), 0 0 80px rgba(31,43,255,.25)",
              padding: "28px 36px",
              fontFamily: MONO,
              fontSize: 27,
              lineHeight: 1.7,
              color: C.paper,
            }}
          >
            {lines.map(([pfx, txt], i) => {
              const s = at + 18 + i * 8;
              const n = Math.max(
                0,
                Math.min(txt.length, Math.floor((frame - s) * 2.2)),
              );
              return (
                <div
                  key={i}
                  style={{
                    whiteSpace: "pre",
                    color: pfx ? C.paper : C.mist,
                    opacity: frame >= s ? 1 : 0,
                  }}
                >
                  <span style={{ color: C.blueText }}>{pfx}</span>
                  {txt.slice(0, n)}
                </div>
              );
            })}
          </div>
        </Reveal>
        <Tag
          at={at + 26}
          style={{ position: "relative", marginTop: 22, color: C.blueText }}
        >
          Termux:API · Android&apos;s own APIs
        </Tag>
      </div>
    </AbsoluteFill>
  );
};

/** Stylised Hermes approval panel drawing itself on. */
const Approval: React.FC<{ at: number; out: number }> = ({ at, out }) => {
  const frame = useCurrentFrame();
  const { v } = useInOut(at, out, 10, 8);
  const draw = interpolate(frame, [at, at + 21], [0, 1], {
    ...clamp,
    easing: EXPO,
  });
  const W = 940;
  const H = 470;
  const per = 2 * (W + H);
  const rows = [
    "Allow once",
    "Allow for this session",
    "Add to permanent allowlist",
    "Deny",
  ];
  const sel = interpolate(frame, [at + 30, at + 40], [0, 1], {
    ...clamp,
    easing: EXPO,
  });
  return (
    <AbsoluteFill
      style={{
        alignItems: "center",
        justifyContent: "center",
        opacity: v,
        translate: "0 70px",
      }}
    >
      <div style={{ position: "relative", width: W, height: H }}>
        <div
          style={{
            position: "absolute",
            inset: 0,
            borderRadius: 26,
            background: "rgba(10,10,18,.8)",
            opacity: draw,
            boxShadow: "0 40px 120px rgba(0,0,0,.6)",
          }}
        />
        <svg
          width={W}
          height={H}
          style={{ position: "absolute", inset: 0, overflow: "visible" }}
        >
          <rect
            x={1}
            y={1}
            width={W - 2}
            height={H - 2}
            rx={26}
            fill="none"
            stroke={C.blue}
            strokeWidth={2.5}
            strokeDasharray={per}
            strokeDashoffset={per * (1 - draw)}
            style={{ filter: "drop-shadow(0 0 10px rgba(31,43,255,.8))" }}
          />
        </svg>
        <div style={{ position: "absolute", inset: 0, padding: "34px 44px" }}>
          <Reveal at={at + 10} rise={12}>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 14,
                ...mono(17, { color: C.paper }),
              }}
            >
              <Icon name="lock" size={24} color={C.blueText} />
              Approval needed · phone_sms_send
            </div>
            <div
              style={{
                fontFamily: DISPLAY,
                fontWeight: 500,
                fontSize: 30,
                color: "rgba(241,241,238,.8)",
                marginTop: 14,
              }}
            >
              Hermes wants to send a text from your SIM.
            </div>
          </Reveal>
          <div
            style={{
              marginTop: 26,
              display: "flex",
              flexDirection: "column",
              gap: 10,
            }}
          >
            {rows.map((r, i) => {
              const p = interpolate(
                frame,
                [at + 16 + i * 3, at + 28 + i * 3],
                [0, 1],
                { ...clamp, easing: EXPO },
              );
              const on = i === 0;
              return (
                <div
                  key={r}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 18,
                    padding: "12px 20px",
                    borderRadius: 14,
                    fontFamily: MONO,
                    fontSize: 25,
                    color: on ? C.paper : C.mist,
                    background: on
                      ? `rgba(31,43,255,${0.85 * sel})`
                      : "transparent",
                    boxShadow: on
                      ? `0 0 ${40 * sel}px rgba(31,43,255,${0.5 * sel})`
                      : undefined,
                    opacity: p,
                    translate: `${(1 - p) * 20}px 0`,
                  }}
                >
                  <span style={{ opacity: 0.7 }}>{i + 1}.</span>
                  {r}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

export const Turn: React.FC = () => {
  const cue = useCues(ID);
  const k2 = cue("k2");
  const k3 = cue("k3");
  const k4 = cue("k4");
  const k5 = cue("k5");
  return (
    <AbsoluteFill style={{ backgroundColor: C.ink }}>
      <FilmField sectionId={ID} intensity={0.6} />

      {/* A · chaos collapses into order, the mark appears (k1) */}
      <Fuse fuseAt={4} outAt={22} />
      <Order at={20} gridAt={32} blueAt={38} collapseAt={52} />
      <Lockup markAt={56} wordAt={66} outAt={k2.s - 8} />

      {/* B · what it is (k2) */}
      <Headline
        top={190}
        text="Your phone's senses, for Hermes."
        start={k2.s}
        stagger={2}
        size={90}
        exitAt={k3.s - 10}
      />
      <Senses at={k2.s + 6} out={k3.s - 10} />

      {/* C · no screen tapping (k3) */}
      <Headline
        top={150}
        text="No screen tapping."
        start={k3.s}
        stagger={2}
        size={112}
        exitAt={k4.s - 10}
      />
      <NoTapping at={k3.s + 8} out={k4.s - 10} />

      {/* D · it always asks first (k4) */}
      <Headline
        top={130}
        text="It always asks first."
        start={k4.s}
        stagger={2}
        size={104}
        accent={["asks"]}
        exitAt={k5.s - 10}
      />
      <Approval at={k4.s + 6} out={k5.s - 10} />

      {/* E · hand-off to the walkthrough (k5); ends on a clean field */}
      <AbsoluteFill
        style={{
          alignItems: "center",
          justifyContent: "center",
          flexDirection: "column",
          gap: 34,
        }}
      >
        <Kinetic
          text="His real day."
          start={k5.s}
          stagger={2}
          size={132}
          exitAt={k5.e + 18}
        />
        <Kinetic
          text="His real phone."
          start={k5.s + 30}
          stagger={2}
          size={132}
          accent={["phone"]}
          exitAt={k5.e + 18}
        />
      </AbsoluteFill>
      <Tag
        at={k5.s + 34}
        out={k5.e + 18}
        style={{ left: 0, right: 0, top: 790, textAlign: "center" }}
      >
        Real phone · moto g34 · Android 15
      </Tag>
    </AbsoluteFill>
  );
};
