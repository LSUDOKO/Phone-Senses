import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { C, DISPLAY, EASE_IN, EXPO, MONO } from "../brand";
import {
  clamp,
  Counter,
  display,
  Drift,
  FilmField,
  Icon,
  IconName,
  mono,
  Pulse,
  Reveal,
  Tag,
  useCues,
  useInOut,
} from "../motion";

const ID = "hood";
const ROW_Y = 250;
const NODES: { x: number; label: string; sub: string; icon: IconName }[] = [
  { x: 250, label: "Hermes", sub: "the agent", icon: "chat" },
  { x: 605, label: "Approval hook", sub: "pre_tool_call", icon: "lock" },
  { x: 960, label: "Signed request", sub: "HMAC-SHA256", icon: "key" },
  { x: 1315, label: "Termux helper", sub: "on the phone", icon: "grid" },
  { x: 1670, label: "Android API", sub: "Termux:API", icon: "battery" },
];

// The real canonical string for GET /v1/status (empty body). Timestamp and nonce are example values.
const CANON: [string, string][] = [
  ["Method", "GET"],
  ["Path", "/v1/status"],
  ["Timestamp", "1794161127"],
  ["Nonce · 16 bytes", "9f2c1e7a4b0d83f6c5a1e09b7d2f4c68"],
  [
    "SHA-256(body)",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  ],
];

/** Pulse position along the node row, as a node index (fractional while travelling). */
const usePulseAt = (keys: [number, number][]) => {
  const frame = useCurrentFrame();
  return interpolate(
    frame,
    keys.map((k) => k[0]),
    keys.map((k) => k[1]),
    { ...clamp, easing: EXPO },
  );
};

const Pipeline: React.FC<{ pos: number; lit: number; returning: boolean }> = ({
  pos,
  lit,
  returning,
}) => {
  const frame = useCurrentFrame();
  const { enter } = useInOut(0, undefined, 18);
  const xAt = (p: number) => {
    const i = Math.min(NODES.length - 2, Math.floor(p));
    return NODES[i].x + (NODES[i + 1].x - NODES[i].x) * (p - i);
  };
  return (
    <AbsoluteFill style={{ opacity: enter }}>
      <svg
        width={1920}
        height={1080}
        style={{ position: "absolute", inset: 0 }}
      >
        {NODES.slice(0, -1).map((n, i) => {
          const done = lit > i;
          return (
            <line
              key={i}
              x1={n.x + 56}
              y1={ROW_Y}
              x2={NODES[i + 1].x - 56}
              y2={ROW_Y}
              stroke={done ? C.blue : "rgba(154,160,180,.45)"}
              strokeWidth={done ? 3 : 2}
              strokeDasharray={done ? undefined : "8 8"}
              style={{
                filter: done
                  ? "drop-shadow(0 0 8px rgba(31,43,255,.9))"
                  : undefined,
              }}
            />
          );
        })}
      </svg>
      {NODES.map((n, i) => {
        const p = interpolate(frame, [i * 3, i * 3 + 14], [0, 1], {
          ...clamp,
          easing: EXPO,
        });
        const active = Math.abs(pos - i) < 0.25;
        const done = lit >= i;
        return (
          <div
            key={n.label}
            style={{
              position: "absolute",
              left: n.x - 130,
              top: ROW_Y - 52,
              width: 260,
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              opacity: p,
              translate: `0 ${(1 - p) * 20}px`,
            }}
          >
            <div
              style={{
                width: 104,
                height: 104,
                borderRadius: 28,
                background: done ? "rgba(31,43,255,.22)" : "rgba(18,19,28,.9)",
                border: `1px solid ${done ? "rgba(139,147,255,.75)" : "rgba(255,255,255,.16)"}`,
                boxShadow: active
                  ? "0 0 60px rgba(31,43,255,.75)"
                  : "0 18px 50px rgba(0,0,0,.5)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: C.paper,
                scale: active ? "1.06" : "1",
              }}
            >
              <Icon name={n.icon} size={46} stroke={1.5} />
            </div>
            <div
              style={{
                fontFamily: DISPLAY,
                fontWeight: 800,
                fontStretch: "112%",
                fontSize: 28,
                color: C.paper,
                marginTop: 18,
                letterSpacing: "-0.02em",
                whiteSpace: "nowrap",
              }}
            >
              {n.label}
            </div>
            <div
              style={{
                ...mono(14),
                marginTop: 4,
                textTransform: i === 1 ? "none" : "uppercase",
              }}
            >
              {n.sub}
            </div>
          </div>
        );
      })}
      {pos >= 0 ? <Pulse x={xAt(pos)} y={ROW_Y} size={20} /> : null}
      {returning ? (
        <div
          style={{
            position: "absolute",
            left: xAt(pos) - 100,
            top: ROW_Y - 110,
            width: 200,
            textAlign: "center",
            ...mono(14, { color: C.blueText }),
          }}
        >
          200 · answer
        </div>
      ) : null}
    </AbsoluteFill>
  );
};

/** h1 · the question */
const Question: React.FC<{ at: number; out: number }> = ({ at, out }) => {
  const frame = useCurrentFrame();
  const q = "What's my phone battery?";
  const n = Math.max(0, Math.min(q.length, Math.floor((frame - at - 6) * 1.6)));
  return (
    <Reveal
      at={at}
      out={out}
      style={{
        position: "absolute",
        left: 0,
        right: 0,
        top: 520,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 30,
      }}
    >
      <div style={mono(16)}>You → Hermes</div>
      <div
        style={{
          padding: "26px 44px",
          borderRadius: 28,
          background: "rgba(241,241,238,.07)",
          border: "1px solid rgba(255,255,255,.14)",
          ...display(64, { fontWeight: 700, letterSpacing: "-0.02em" }),
        }}
      >
        {q.slice(0, n)}
        <span
          style={{
            opacity: n < q.length || Math.floor(frame / 9) % 2 ? 1 : 0,
            color: C.blueText,
          }}
        >
          ▌
        </span>
      </div>
      <Reveal at={at + 46} rise={14}>
        <div
          style={{
            ...mono(20, { color: C.paper, textTransform: "none" }),
            padding: "10px 20px",
            borderRadius: 999,
            border: "1px solid rgba(139,147,255,.5)",
            background: "rgba(31,43,255,.18)",
          }}
        >
          tool call · phone_status
        </div>
      </Reveal>
    </Reveal>
  );
};

/** h2 · the gate: reads pass, four actions are held for approval */
const Gate: React.FC<{ at: number; out: number }> = ({ at, out }) => {
  const frame = useCurrentFrame();
  const open = interpolate(frame, [at + 14, at + 26], [0, 1], {
    ...clamp,
    easing: EXPO,
  });
  const tok = interpolate(frame, [at + 22, at + 40], [0, 1], {
    ...clamp,
    easing: EXPO,
  });
  const gated = [
    "phone_sms_send",
    "phone_call",
    "phone_photo",
    "phone_otp_reveal",
  ];
  return (
    <Reveal
      at={at}
      out={out}
      style={{ position: "absolute", left: 0, right: 0, top: 470 }}
    >
      <svg
        width={1920}
        height={120}
        style={{
          position: "absolute",
          left: 0,
          top: -150,
          overflow: "visible",
        }}
      >
        <path
          d={`M605 50 L605 100 L460 100 L460 140`}
          fill="none"
          stroke={C.blue}
          strokeWidth={2}
        />
        <path
          d={`M605 100 L1180 100 L1180 140`}
          fill="none"
          stroke="rgba(154,160,180,.45)"
          strokeWidth={2}
          strokeDasharray="8 8"
        />
      </svg>
      {/* read passes */}
      <div
        style={{
          position: "absolute",
          left: 200,
          width: 520,
          height: 300,
          borderRadius: 26,
          border: "1px solid rgba(139,147,255,.45)",
          background: "rgba(31,43,255,.08)",
        }}
      >
        <div
          style={{
            position: "absolute",
            left: 28,
            top: 22,
            ...mono(15, { color: C.blueText }),
          }}
        >
          Read · passes
        </div>
        {[-1, 1].map((d) => (
          <div
            key={d}
            style={{
              position: "absolute",
              left: 255 + d * (12 + open * 70),
              top: 70,
              width: 10,
              height: 170,
              borderRadius: 5,
              background: C.paper,
              opacity: 0.85,
            }}
          />
        ))}
        <div
          style={{
            position: "absolute",
            left: interpolate(tok, [0, 1], [10, 300]),
            top: 135,
            padding: "10px 18px",
            borderRadius: 999,
            background: C.blue,
            boxShadow: "0 0 30px rgba(31,43,255,.7)",
            ...mono(18, { color: C.paper, textTransform: "none" }),
          }}
        >
          phone_status
        </div>
      </div>
      {/* gated side branch */}
      <div
        style={{
          position: "absolute",
          left: 860,
          width: 640,
          height: 300,
          borderRadius: 26,
          border: "1px dashed rgba(154,160,180,.4)",
          background: "rgba(255,255,255,.03)",
          padding: "22px 28px",
        }}
      >
        <div style={{ ...mono(15) }}>4 actions gated · asks you first</div>
        <div
          style={{
            marginTop: 18,
            display: "flex",
            flexDirection: "column",
            gap: 10,
          }}
        >
          {gated.map((g, i) => {
            const p = interpolate(
              frame,
              [at + 30 + i * 3, at + 40 + i * 3],
              [0, 1],
              { ...clamp, easing: EXPO },
            );
            return (
              <div
                key={g}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 14,
                  opacity: p * 0.75,
                  translate: `${(1 - p) * 20}px 0`,
                  ...mono(22, {
                    color: C.paper,
                    textTransform: "none",
                    letterSpacing: "0.02em",
                  }),
                }}
              >
                <Icon name="lock" size={22} color={C.mist} />
                {g}
                <span style={{ marginLeft: "auto", ...mono(13) }}>
                  → approval panel
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </Reveal>
  );
};

/** h3/h4 · the canonical string, signed */
const Canonical: React.FC<{ at: number; replayAt: number; out: number }> = ({
  at,
  replayAt,
  out,
}) => {
  const frame = useCurrentFrame();
  const hi = interpolate(frame, [replayAt, replayAt + 10], [0, 1], {
    ...clamp,
    easing: EXPO,
  });
  const sig = interpolate(frame, [at + 62, at + 76], [0, 1], {
    ...clamp,
    easing: EXPO,
  });
  return (
    <Reveal
      at={at}
      out={out}
      style={{ position: "absolute", left: 160, top: 430 }}
    >
      <div style={{ ...mono(14), marginBottom: 14 }}>
        The string that gets signed · real format
      </div>
      <div
        style={{
          width: 1600,
          borderRadius: 22,
          background: "rgba(10,10,18,.82)",
          border: "1px solid rgba(255,255,255,.14)",
          padding: "18px 0",
        }}
      >
        {CANON.map(([label, val], i) => {
          const s = at + 4 + i * 7;
          const n = Math.max(
            0,
            Math.min(val.length, Math.floor((frame - s) * 3)),
          );
          const isHot = (i === 2 || i === 3) && hi > 0;
          return (
            <div
              key={label}
              style={{
                display: "flex",
                alignItems: "center",
                padding: "7px 32px",
                background: isHot
                  ? `rgba(31,43,255,${0.28 * hi})`
                  : "transparent",
                opacity: frame >= s ? 1 : 0,
              }}
            >
              <span style={{ width: 230, flexShrink: 0, ...mono(14) }}>
                {label}
              </span>
              <span
                style={{
                  fontFamily: MONO,
                  fontSize: 27,
                  color: i === 0 ? C.blueText : C.paper,
                  whiteSpace: "pre",
                  letterSpacing: "0.01em",
                }}
              >
                {val.slice(0, n)}
              </span>
              {i === 2 ? (
                <span
                  style={{
                    marginLeft: "auto",
                    opacity: hi,
                    ...mono(15, { color: C.paper }),
                  }}
                >
                  timestamp ±60 s
                </span>
              ) : null}
              {i === 3 ? (
                <span
                  style={{
                    marginLeft: "auto",
                    opacity: hi,
                    ...mono(15, { color: C.paper }),
                  }}
                >
                  nonce: replay rejected
                </span>
              ) : null}
            </div>
          );
        })}
      </div>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 22,
          marginTop: 26,
          opacity: sig,
          translate: `${(1 - sig) * -20}px 0`,
        }}
      >
        <span style={{ fontFamily: MONO, fontSize: 27, color: C.paper }}>
          HMAC-SHA256( secret )
        </span>
        <svg width={70} height={20}>
          <path
            d="M0 10 H60 M50 2 L62 10 L50 18"
            fill="none"
            stroke={C.blueText}
            strokeWidth={2.5}
          />
        </svg>
        <span
          style={{
            fontFamily: MONO,
            fontSize: 27,
            color: C.paper,
            padding: "6px 16px",
            borderRadius: 10,
            background: C.blue,
          }}
        >
          X-PS-Signature
        </span>
        <span style={{ marginLeft: 26, ...mono(15, { color: C.blueText }) }}>
          secret never sent
        </span>
      </div>
    </Reveal>
  );
};

/** h4 · a replayed copy bounces off the helper */
const Replay: React.FC<{ at: number }> = ({ at }) => {
  const frame = useCurrentFrame();
  const go = interpolate(frame, [at, at + 14], [0, 1], {
    ...clamp,
    easing: EASE_IN,
  });
  const back = interpolate(frame, [at + 14, at + 30], [0, 1], {
    ...clamp,
    easing: EXPO,
  });
  const fade = interpolate(frame, [at + 60, at + 70], [1, 0], clamp);
  if (frame < at) return null;
  const x = 900 + go * 200 - back * 120;
  return (
    <div
      style={{
        position: "absolute",
        left: x,
        top: ROW_Y - 112,
        opacity: fade,
        display: "flex",
        alignItems: "center",
        gap: 14,
      }}
    >
      <div
        style={{
          padding: "8px 14px",
          borderRadius: 10,
          border: "1px dashed rgba(241,241,238,.5)",
          ...mono(17, { color: C.paper }),
        }}
      >
        replayed request
      </div>
      {back > 0.2 ? (
        <div style={{ ...mono(18, { color: C.paper }), opacity: back }}>
          401 · nonce reused
        </div>
      ) : null}
    </div>
  );
};

/** h5 · the helper runs one fixed command */
const Helper: React.FC<{ at: number; out: number }> = ({ at, out }) => {
  const chips = [
    "GET /v1/status",
    "termux-battery-status",
    "Android battery API",
  ];
  return (
    <Reveal
      at={at}
      out={out}
      style={{
        position: "absolute",
        left: 0,
        right: 0,
        top: 540,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 34,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 26 }}>
        {chips.map((c, i) => (
          <React.Fragment key={c}>
            {i > 0 ? (
              <svg width={70} height={20}>
                <path
                  d="M0 10 H60 M50 2 L62 10 L50 18"
                  fill="none"
                  stroke={C.blueText}
                  strokeWidth={2.5}
                />
              </svg>
            ) : null}
            <Reveal at={at + 4 + i * 8} rise={16}>
              <div
                style={{
                  padding: "18px 28px",
                  borderRadius: 18,
                  fontFamily: MONO,
                  fontSize: 30,
                  color: C.paper,
                  background:
                    i === 2 ? "rgba(31,43,255,.3)" : "rgba(10,10,18,.85)",
                  border: `1px solid ${i === 2 ? "rgba(139,147,255,.7)" : "rgba(255,255,255,.16)"}`,
                }}
              >
                {c}
              </div>
            </Reveal>
          </React.Fragment>
        ))}
      </div>
      <Reveal at={at + 30} rise={10}>
        <div style={mono(16)}>Stdlib Python · fixed command · no shell</div>
      </Reveal>
    </Reveal>
  );
};

/** h6 · measured latency */
const Latency: React.FC<{ at: number }> = ({ at }) => (
  <div
    style={{
      position: "absolute",
      left: 0,
      right: 0,
      top: 470,
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      gap: 18,
    }}
  >
    <Reveal at={at} rise={30}>
      <div style={{ display: "flex", alignItems: "baseline", gap: 18 }}>
        <Counter to={1.6} decimals={1} at={at} style={display(220)} />
        <span style={display(110)}>s</span>
      </div>
    </Reveal>
    <Reveal at={at + 8} rise={20}>
      <div
        style={display(46, {
          fontWeight: 600,
          fontStretch: "110%",
          letterSpacing: "-0.01em",
          color: "rgba(241,241,238,.8)",
        })}
      >
        median · real <span style={{ color: C.blueText }}>moto g34</span>
      </div>
    </Reveal>
    <Reveal at={at + 16} rise={10}>
      <div style={mono(15)}>
        GET /v1/status · 8 runs · min 1.59 s · max 2.35 s
      </div>
    </Reveal>
  </div>
);

export const UnderTheHood: React.FC = () => {
  const cue = useCues(ID);
  const h1 = cue("h1");
  const h2 = cue("h2");
  const h3 = cue("h3");
  const h4 = cue("h4");
  const h5 = cue("h5");
  const h6 = cue("h6");
  const frame = useCurrentFrame();
  const pos = usePulseAt([
    [0, 0],
    [h2.s, 0],
    [h2.s + 18, 1],
    [h3.s, 1],
    [h3.s + 18, 2],
    [h5.s, 2],
    [h5.s + 16, 3],
    [h5.s + 40, 3],
    [h5.s + 56, 4],
    [h6.s, 4],
    [h6.s + 26, 0],
  ]);
  const lit = frame < h6.s ? pos : 4;
  return (
    <AbsoluteFill style={{ backgroundColor: C.ink }}>
      <FilmField sectionId={ID} intensity={0.7} />
      <Tag at={4} style={{ left: 96, top: 64 }}>
        <span style={{ color: C.blueText }}>Under the hood</span>
        &nbsp;&nbsp;·&nbsp;&nbsp;one real request
      </Tag>
      <Pipeline
        pos={frame >= 20 ? pos : -1}
        lit={lit}
        returning={frame >= h6.s && frame < h6.s + 40}
      />
      <Question at={h1.s + 8} out={h2.s - 8} />
      <Gate at={h2.s} out={h3.s - 8} />
      <Canonical at={h3.s} replayAt={h4.s} out={h5.s - 8} />
      <Replay at={h4.s + 12} />
      <Helper at={h5.s} out={h6.s - 8} />
      <Drift from={h6.s} to={600} amount={0.04}>
        <Latency at={h6.s + 4} />
      </Drift>
    </AbsoluteFill>
  );
};
