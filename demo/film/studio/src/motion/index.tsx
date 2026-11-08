import React from "react";
import {
  AbsoluteFill,
  interpolate,
  random,
  Sequence,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { C, DISPLAY, EASE_IN, EXPO, Field, Kinetic, MONO } from "../brand";
import vo from "../data/vo.json";

export const clamp = {
  extrapolateLeft: "clamp",
  extrapolateRight: "clamp",
} as const;

type Section = (typeof vo.sections)[number];

const section = (id: string): Section => {
  const s = vo.sections.find((x) => x.id === id);
  if (!s) throw new Error(`vo.json has no section "${id}"`);
  return s;
};

/** Section length in frames. */
export const sectionFrames = (id: string, fps: number) => {
  const s = section(id);
  return Math.round((s.end - s.start) * fps);
};

/** Section start on the film timeline, in frames. */
export const sectionStartFrame = (id: string, fps: number) =>
  Math.round(section(id).start * fps);

/** VO cues for one section, in frames relative to the section start: cue("p3").s / .e */
export const useCues = (id: string) => {
  const { fps } = useVideoConfig();
  const s = section(id);
  return (lineId: string) => {
    const l = s.lines.find((x) => x.id === lineId);
    if (!l) throw new Error(`vo.json section "${id}" has no line "${lineId}"`);
    return {
      s: Math.round((l.start - s.start) * fps),
      e: Math.round((l.end - s.start) * fps),
    };
  };
};

/** Brand field that keeps drifting on film time, so blobs don't jump at section cuts. */
export const FilmField: React.FC<{
  sectionId: string;
  intensity?: number;
  grid?: boolean;
}> = ({ sectionId, intensity, grid }) => {
  const { fps } = useVideoConfig();
  return (
    <Sequence
      from={-sectionStartFrame(sectionId, fps)}
      layout="none"
      name="Field"
    >
      <Field intensity={intensity} grid={grid} />
    </Sequence>
  );
};

/** Entrance (EXPO, 14f) and optional quick exit (EASE_IN, 8f): returns 0..1 visibility plus exit amount. */
export const useInOut = (
  inAt: number,
  outAt?: number,
  inDur = 14,
  outDur = 8,
) => {
  const frame = useCurrentFrame();
  const enter = interpolate(frame, [inAt, inAt + inDur], [0, 1], {
    ...clamp,
    easing: EXPO,
  });
  const exit =
    outAt === undefined
      ? 0
      : interpolate(frame, [outAt, outAt + outDur], [0, 1], {
          ...clamp,
          easing: EASE_IN,
        });
  return { enter, exit, v: enter * (1 - exit) };
};

/** Fade/rise/blur in, fade/lift out. */
export const Reveal: React.FC<{
  at: number;
  out?: number;
  rise?: number;
  style?: React.CSSProperties;
  children: React.ReactNode;
}> = ({ at, out, rise = 30, style, children }) => {
  const { enter, exit, v } = useInOut(at, out);
  return (
    <div
      style={{
        opacity: v,
        translate: `0 ${(1 - enter) * rise - exit * 20}px`,
        filter: enter < 1 ? `blur(${(1 - enter) * 8}px)` : undefined,
        ...style,
      }}
    >
      {children}
    </div>
  );
};

const group = (s: string) => s.replace(/\B(?=(\d{3})+(?!\d))/g, ",");

/** Number roll (900 ms, brand ease). */
export const Counter: React.FC<{
  to: number;
  from?: number;
  at: number;
  decimals?: number;
  dur?: number;
  prefix?: string;
  suffix?: string;
  style?: React.CSSProperties;
}> = ({
  to,
  from = 0,
  at,
  decimals = 0,
  dur = 27,
  prefix = "",
  suffix = "",
  style,
}) => {
  const frame = useCurrentFrame();
  const v = interpolate(frame, [at, at + dur], [from, to], {
    ...clamp,
    easing: EXPO,
  });
  const [i, d] = v.toFixed(decimals).split(".");
  return (
    <span style={{ fontVariantNumeric: "tabular-nums", ...style }}>
      {prefix}
      {group(i)}
      {d ? `.${d}` : ""}
      {suffix}
    </span>
  );
};

/** Big display text block (not word-split). */
export const display = (
  size: number,
  extra?: React.CSSProperties,
): React.CSSProperties => ({
  fontFamily: DISPLAY,
  fontWeight: 800,
  fontStretch: "118%",
  fontSize: size,
  lineHeight: 0.96,
  letterSpacing: "-0.04em",
  color: C.paper,
  ...extra,
});

export const mono = (
  size: number,
  extra?: React.CSSProperties,
): React.CSSProperties => ({
  fontFamily: MONO,
  fontWeight: 500,
  fontSize: size,
  letterSpacing: "0.08em",
  textTransform: "uppercase",
  color: C.mist,
  lineHeight: 1.45,
  ...extra,
});

/** Source line: Geist Mono 14 px, Mist, bottom-left, max ~680 px wide so it stays clear of burned-in captions. */
export const SourceLine: React.FC<{
  at: number;
  out?: number;
  children: React.ReactNode;
}> = ({ at, out, children }) => {
  const { v } = useInOut(at, out, 12, 8);
  return (
    <div
      style={{
        position: "absolute",
        left: 96,
        bottom: 128,
        maxWidth: 680,
        ...mono(14, { letterSpacing: "0.06em" }),
        opacity: v,
      }}
    >
      <span style={{ color: C.paper }}>SOURCE&nbsp;&nbsp;</span>
      {children}
    </div>
  );
};

/** Corner label that can also exit. */
export const Tag: React.FC<{
  at: number;
  out?: number;
  style?: React.CSSProperties;
  children: React.ReactNode;
}> = ({ at, out, style, children }) => {
  const { enter, v } = useInOut(at, out, 12, 8);
  return (
    <div
      style={{
        position: "absolute",
        ...mono(16, { color: "rgba(241,241,238,.78)" }),
        opacity: v,
        translate: `0 ${(1 - enter) * 10}px`,
        ...style,
      }}
    >
      {children}
    </div>
  );
};

/** Deterministic shake for alarm moments (no red: motion carries it). */
export const useShake = (from: number, to: number, amp = 8, seed = "shake") => {
  const frame = useCurrentFrame();
  if (frame < from || frame > to) return "0px 0px";
  const k = 1 - (frame - from) / Math.max(1, to - from);
  return `${(random(`${seed}x${frame}`) - 0.5) * 2 * amp * k}px ${(random(`${seed}y${frame}`) - 0.5) * 2 * amp * k}px`;
};

/** Hard black dip for the last n frames of a section. */
export const DipOut: React.FC<{ at: number; dur?: number }> = ({
  at,
  dur = 4,
}) => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill
      style={{
        background: C.ink,
        opacity: interpolate(frame, [at, at + dur], [0, 1], clamp),
        pointerEvents: "none",
      }}
    />
  );
};

/* ---------- line icons (24×24 viewBox, stroke = currentColor) ---------- */
const ICONS: Record<string, React.ReactNode> = {
  bell: <path d="M6 16V11a6 6 0 0 1 12 0v5l1.5 2h-15zM10 20.5a2 2 0 0 0 4 0" />,
  sms: <path d="M4 5h16v11H9l-4 3.5V16H4z M8 9.5h8 M8 12.5h5" />,
  rupee: <path d="M7 4.5h10 M7 8.5h10 M7 4.5h3.5a4 4 0 0 1 0 8H7l8 7" />,
  parcel: <path d="M4 8l8-4 8 4v8l-8 4-8-4z M4 8l8 4 8-4 M12 12v8 M8 6l8 4" />,
  call: (
    <path d="M6.5 4h3l1.5 4-2 1.5a10 10 0 0 0 5.5 5.5l1.5-2 4 1.5v3a2 2 0 0 1-2 2A15 15 0 0 1 4.5 6a2 2 0 0 1 2-2z" />
  ),
  battery: <path d="M3 8h15v8H3z M18 10.5h2.5v3H18 M5.5 10.5h7v3h-7" />,
  pin: (
    <path d="M12 21s-6.5-6-6.5-11a6.5 6.5 0 0 1 13 0c0 5-6.5 11-6.5 11z M12 7.5a2.5 2.5 0 1 1 0 5 2.5 2.5 0 0 1 0-5z" />
  ),
  camera: (
    <path d="M3 8h4l2-2.5h6L17 8h4v11H3z M12 10a3.5 3.5 0 1 1 0 7 3.5 3.5 0 0 1 0-7z" />
  ),
  key: (
    <path d="M8 14.5a3.5 3.5 0 1 1 0-7 3.5 3.5 0 0 1 0 7z M11.5 11H21 M18 11v3 M15 11v2.5" />
  ),
  lock: <path d="M5 11h14v10H5z M8 11V8a4 4 0 0 1 8 0v3 M12 15v2.5" />,
  mail: <path d="M3 6h18v12H3z M3 6l9 7 9-7" />,
  chat: (
    <path d="M5 5h14a1 1 0 0 1 1 1v9a1 1 0 0 1-1 1h-7l-4 3.5V16H5a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1z" />
  ),
  cal: <path d="M4 6h16v14H4z M4 10h16 M8 3.5v4 M16 3.5v4" />,
  card: <path d="M3 6h18v12H3z M3 10h18 M6 14.5h5" />,
  grid: <path d="M4 4h6v6H4z M14 4h6v6h-6z M4 14h6v6H4z M14 14h6v6h-6z" />,
};
export type IconName = keyof typeof ICONS;

export const Icon: React.FC<{
  name: IconName;
  size?: number;
  color?: string;
  stroke?: number;
  style?: React.CSSProperties;
}> = ({ name, size = 28, color = "currentColor", stroke = 1.6, style }) => (
  <svg
    viewBox="0 0 24 24"
    width={size}
    height={size}
    fill="none"
    stroke={color}
    strokeWidth={stroke}
    strokeLinejoin="round"
    strokeLinecap="round"
    style={style}
  >
    {ICONS[name]}
  </svg>
);

/* ---------- generic notification card (no real personal data) ---------- */
export type Notif = {
  app: string;
  icon: IconName;
  title: string;
  body?: string;
  time?: string;
};

export const NOTIFS: Notif[] = [
  {
    app: "Messages",
    icon: "sms",
    title: "AX-BANKIN",
    body: "UPI debit of Rs ••• · Ref •••••",
    time: "now",
  },
  {
    app: "College group",
    icon: "chat",
    title: "Final year · CSE",
    body: "47 new messages",
    time: "1m",
  },
  {
    app: "Phone",
    icon: "call",
    title: "Missed calls",
    body: "Mom · 3 missed calls",
    time: "2m",
  },
  {
    app: "Courier",
    icon: "parcel",
    title: "Out for delivery",
    body: "Arriving today by 6 pm",
    time: "4m",
  },
  {
    app: "Calendar",
    icon: "cal",
    title: "Exam · Data Structures",
    body: "Tomorrow · 10:00",
    time: "6m",
  },
  {
    app: "Mail",
    icon: "mail",
    title: "12 new emails",
    body: "Placement cell, Library, +10",
    time: "8m",
  },
  {
    app: "Bills",
    icon: "card",
    title: "Recharge due",
    body: "Your plan expires in 2 days",
    time: "9m",
  },
  {
    app: "Battery",
    icon: "battery",
    title: "Battery low",
    body: "18% remaining",
    time: "11m",
  },
  {
    app: "Messages",
    icon: "sms",
    title: "VM-PAYALR",
    body: "Rs ••• credited by UPI",
    time: "12m",
  },
  {
    app: "Food",
    icon: "bell",
    title: "Your order is on the way",
    body: "Rider is 5 min away",
    time: "14m",
  },
  {
    app: "Messages",
    icon: "sms",
    title: "+91 9•••• •••••",
    body: "Are you coming to the library?",
    time: "15m",
  },
  {
    app: "Wallet",
    icon: "rupee",
    title: "Cashback unlocked",
    body: "Tap to claim before midnight",
    time: "17m",
  },
];

export const NotifCard: React.FC<{
  n: Notif;
  width?: number;
  scale?: number;
  tone?: "glass" | "grey";
  style?: React.CSSProperties;
}> = ({ n, width = 520, scale = 1, tone = "glass", style }) => (
  <div
    style={{
      width,
      padding: `${18 * scale}px ${22 * scale}px`,
      borderRadius: 22 * scale,
      background:
        tone === "glass" ? "rgba(28,29,38,.86)" : "rgba(60,62,72,.55)",
      border: "1px solid rgba(255,255,255,.12)",
      boxShadow:
        "0 24px 60px rgba(0,0,0,.55), inset 0 1px 0 rgba(255,255,255,.08)",
      display: "flex",
      gap: 16 * scale,
      alignItems: "flex-start",
      ...style,
    }}
  >
    <div
      style={{
        width: 44 * scale,
        height: 44 * scale,
        borderRadius: 12 * scale,
        flexShrink: 0,
        background: "rgba(255,255,255,.08)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        color: C.paper,
      }}
    >
      <Icon name={n.icon} size={24 * scale} />
    </div>
    <div style={{ flex: 1, minWidth: 0 }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          ...mono(13 * scale, { letterSpacing: "0.06em" }),
        }}
      >
        <span>{n.app}</span>
        <span>{n.time}</span>
      </div>
      <div
        style={{
          fontFamily: DISPLAY,
          fontWeight: 700,
          fontStretch: "105%",
          fontSize: 24 * scale,
          color: C.paper,
          marginTop: 2 * scale,
          whiteSpace: "nowrap",
          overflow: "hidden",
          textOverflow: "ellipsis",
        }}
      >
        {n.title}
      </div>
      {n.body ? (
        <div
          style={{
            fontFamily: DISPLAY,
            fontWeight: 400,
            fontSize: 21 * scale,
            color: "rgba(241,241,238,.66)",
            marginTop: 2 * scale,
            whiteSpace: "nowrap",
            overflow: "hidden",
            textOverflow: "ellipsis",
          }}
        >
          {n.body}
        </div>
      ) : null}
    </div>
  </div>
);

/** Ultramarine travelling pulse dot with a soft halo. */
export const Pulse: React.FC<{
  x: number;
  y: number;
  size?: number;
  opacity?: number;
}> = ({ x, y, size = 18, opacity = 1 }) => (
  <div
    style={{
      position: "absolute",
      left: x - size / 2,
      top: y - size / 2,
      width: size,
      height: size,
      borderRadius: size,
      background: "#fff",
      boxShadow: `0 0 0 4px ${C.blue}, 0 0 30px 10px rgba(31,43,255,.75), 0 0 80px 30px rgba(31,43,255,.35)`,
      opacity,
    }}
  />
);

/** RGB-split + slice glitch in ink/ultramarine only. Active on the given [from, to] frame windows. */
export const Glitch: React.FC<{
  windows: [number, number][];
  seed?: string;
  amp?: number;
  children: React.ReactNode;
  style?: React.CSSProperties;
}> = ({ windows, seed = "g", amp = 14, children, style }) => {
  const frame = useCurrentFrame();
  const on = windows.some(([a, b]) => frame >= a && frame <= b);
  const r = (k: string) => random(`${seed}${k}${frame}`) - 0.5;
  return (
    <div style={{ position: "relative", ...style }}>
      <div style={{ opacity: on ? 0.85 : 1 }}>{children}</div>
      {on ? (
        <>
          <div
            style={{
              position: "absolute",
              inset: 0,
              translate: `${r("b") * amp * 2}px 0`,
              mixBlendMode: "screen",
              opacity: 0.9,
              filter: "sepia(1) hue-rotate(190deg) saturate(8) brightness(.8)",
            }}
          >
            {children}
          </div>
          {[0, 1, 2].map((i) => {
            const top = Math.floor(random(`${seed}t${i}${frame}`) * 80);
            const h = 6 + Math.floor(random(`${seed}h${i}${frame}`) * 18);
            return (
              <div
                key={i}
                style={{
                  position: "absolute",
                  inset: 0,
                  clipPath: `inset(${top}% 0 ${Math.max(0, 100 - top - h)}% 0)`,
                  translate: `${r(`s${i}`) * amp * 4}px 0`,
                }}
              >
                {children}
              </div>
            );
          })}
        </>
      ) : null}
    </div>
  );
};

/** Full-width centred Kinetic headline (Kinetic inside a fit-content flex parent mis-measures its gaps and wraps early). */
export const Headline: React.FC<
  { top: number } & React.ComponentProps<typeof Kinetic>
> = ({ top, ...k }) => (
  <div
    style={{
      position: "absolute",
      left: 96,
      right: 96,
      top,
      display: "flex",
      justifyContent: "center",
    }}
  >
    <div style={{ width: "100%" }}>
      <Kinetic maxWidth={1728} {...k} />
    </div>
  </div>
);

/** Slow push-in so long holds never feel frozen. Stops (clamps) at `to`. */
export const Drift: React.FC<{
  from: number;
  to: number;
  amount?: number;
  children: React.ReactNode;
}> = ({ from, to, amount = 0.035, children }) => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill
      style={{
        scale: `${interpolate(frame, [from, to], [1, 1 + amount], clamp)}`,
      }}
    >
      {children}
    </AbsoluteFill>
  );
};
