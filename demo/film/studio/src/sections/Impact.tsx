import React from "react";
import { AbsoluteFill, interpolate, random, useCurrentFrame } from "remotion";
import { C, DISPLAY, EASE_IN, EXPO } from "../brand";
import {
  clamp,
  Counter,
  display,
  Drift,
  FilmField,
  Headline,
  Icon,
  IconName,
  mono,
  NOTIFS,
  NotifCard,
  Reveal,
  SourceLine,
  Tag,
  useCues,
  useInOut,
} from "../motion";

const ID = "impact";
// From the brief; README/RESEARCH.md may lag (22 tools / 129 tests). Re-count before release.
const TOOLS = 25;
const TESTS = 186;

/** Before | Now split. */
const Split: React.FC<{ at: number; nowAt: number; out: number }> = ({
  at,
  nowAt,
  out,
}) => {
  const frame = useCurrentFrame();
  const { v } = useInOut(at, out, 14, 8);
  const wipe = interpolate(frame, [nowAt, nowAt + 18], [0, 1], {
    ...clamp,
    easing: EXPO,
  });
  const dimLeft = interpolate(frame, [nowAt, nowAt + 18], [1, 0.45], clamp);
  const jf = Math.floor(frame / 2.5);
  const answer = [
    "1 scam text flagged · don't tap the link",
    "Battery 100% · no missed calls",
    "7 unread bank & service texts",
    "Spending sorted by category",
  ];
  return (
    <AbsoluteFill style={{ opacity: v }}>
      {/* BEFORE */}
      <div
        style={{
          position: "absolute",
          left: 96,
          top: 190,
          width: 780,
          height: 700,
          opacity: dimLeft,
          filter: "grayscale(1)",
        }}
      >
        <div style={mono(16, { color: C.mist })}>Before</div>
        <div
          style={{
            position: "relative",
            height: 420,
            marginTop: 20,
            overflow: "hidden",
          }}
        >
          {Array.from({ length: 14 }).map((_, i) => {
            const s = at + i * 3;
            const p = interpolate(frame, [s, s + 10], [0, 1], {
              ...clamp,
              easing: EXPO,
            });
            return (
              <div
                key={i}
                style={{
                  position: "absolute",
                  left:
                    20 +
                    random(`ix${i}`) * 240 +
                    (random(`jx${i}${jf}`) - 0.5) * 2,
                  top: random(`iy${i}`) * 330,
                  rotate: `${(random(`ir${i}`) - 0.5) * 10}deg`,
                  opacity: p * 0.9,
                  translate: `0 ${(1 - p) * 80}px`,
                }}
              >
                <NotifCard
                  n={NOTIFS[(i + 3) % NOTIFS.length]}
                  width={460}
                  scale={0.8}
                  tone="grey"
                />
              </div>
            );
          })}
        </div>
        <div style={{ ...display(54, { fontStretch: "112%" }), marginTop: 30 }}>
          Hundreds of notifications.
        </div>
        <div
          style={{
            ...display(34, {
              fontWeight: 500,
              fontStretch: "105%",
              letterSpacing: "-0.01em",
              color: C.mist,
            }),
            marginTop: 14,
          }}
        >
          An agent that couldn&apos;t see them.
        </div>
      </div>
      {/* divider */}
      <div
        style={{
          position: "absolute",
          left: 960,
          top: 190,
          height: 680,
          borderLeft: "1px dashed rgba(241,241,238,.22)",
        }}
      />
      <div
        style={{
          position: "absolute",
          left: 1040,
          top: 190,
          opacity: 1 - wipe,
          ...mono(16),
        }}
      >
        Hermes
      </div>
      <div
        style={{
          position: "absolute",
          left: 1040,
          top: 250,
          opacity: 1 - wipe,
          ...mono(26, { textTransform: "none", letterSpacing: "0.02em" }),
        }}
      >
        hermes &gt;{" "}
        <span style={{ opacity: Math.floor(frame / 9) % 2 ? 1 : 0 }}>▌</span>
      </div>
      {/* NOW */}
      <div
        style={{
          position: "absolute",
          left: 1040,
          top: 190,
          width: 784,
          height: 720,
          clipPath: `inset(0 ${(1 - wipe) * 100}% 0 0)`,
        }}
      >
        <div style={mono(16, { color: C.blueText })}>Now</div>
        <div
          style={{
            marginTop: 20,
            display: "flex",
            flexDirection: "column",
            gap: 18,
          }}
        >
          <div
            style={{
              alignSelf: "flex-end",
              padding: "16px 26px",
              borderRadius: 22,
              background: "rgba(241,241,238,.08)",
              border: "1px solid rgba(255,255,255,.14)",
              ...display(32, {
                fontWeight: 600,
                fontStretch: "105%",
                letterSpacing: "-0.01em",
              }),
            }}
          >
            Give me my phone brief.
          </div>
          <div
            style={{
              padding: "22px 28px",
              borderRadius: 22,
              background: "rgba(31,43,255,.9)",
              boxShadow:
                "0 30px 80px rgba(31,43,255,.35), inset 0 1px 0 rgba(255,255,255,.3)",
            }}
          >
            <div style={mono(14, { color: "rgba(241,241,238,.8)" })}>
              Hermes · from his phone
            </div>
            {answer.map((a, i) => {
              const p = interpolate(
                frame,
                [nowAt + 10 + i * 4, nowAt + 22 + i * 4],
                [0, 1],
                { ...clamp, easing: EXPO },
              );
              return (
                <div
                  key={a}
                  style={{
                    fontFamily: DISPLAY,
                    fontWeight: i === 0 ? 700 : 500,
                    fontSize: 29,
                    color: C.paper,
                    marginTop: 12,
                    opacity: p,
                    translate: `0 ${(1 - p) * 14}px`,
                  }}
                >
                  {a}
                </div>
              );
            })}
          </div>
        </div>
        <div style={{ ...display(54, { fontStretch: "112%" }), marginTop: 34 }}>
          One question.
        </div>
        <div
          style={{
            ...display(34, {
              fontWeight: 500,
              fontStretch: "105%",
              letterSpacing: "-0.01em",
              color: C.mist,
            }),
            marginTop: 14,
          }}
        >
          Hermes knows his whole day.
        </div>
      </div>
    </AbsoluteFill>
  );
};

/** 18.6 vs 10.7 mean steps (Gu et al., the approach, not Phone Senses). */
const Steps: React.FC<{ at: number; out: number }> = ({ at, out }) => {
  const frame = useCurrentFrame();
  const arrow = interpolate(frame, [at + 30, at + 44], [0, 1], {
    ...clamp,
    easing: EXPO,
  });
  return (
    <Reveal
      at={at}
      out={out}
      style={{
        position: "absolute",
        left: 0,
        right: 0,
        top: 440,
        display: "flex",
        justifyContent: "center",
        alignItems: "flex-end",
        gap: 70,
      }}
    >
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
        }}
      >
        <Counter
          to={18.6}
          decimals={1}
          at={at + 4}
          style={display(200, { color: C.mist })}
        />
        <div style={{ ...mono(17), marginTop: 18 }}>Screen agents</div>
      </div>
      <svg
        width={140}
        height={60}
        style={{ marginBottom: 120, opacity: arrow }}
      >
        <path
          d={`M0 30 H${120 * arrow} M${120 * arrow - 16} 14 L${120 * arrow + 2} 30 L${120 * arrow - 16} 46`}
          fill="none"
          stroke={C.blueText}
          strokeWidth={4}
          strokeLinecap="round"
        />
      </svg>
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
        }}
      >
        <Reveal at={at + 30} rise={20}>
          <Counter
            to={10.7}
            from={18.6}
            decimals={1}
            at={at + 34}
            style={display(200, { color: C.blueText })}
          />
          <div
            style={{
              ...mono(17, { color: C.blueText }),
              marginTop: 18,
              textAlign: "center",
            }}
          >
            Command-line agents
          </div>
        </Reveal>
      </div>
    </Reveal>
  );
};

/** 4 actions ask first: icons lock in. */
const Gated: React.FC<{ at: number; out: number }> = ({ at, out }) => {
  const frame = useCurrentFrame();
  const items: [IconName, string][] = [
    ["sms", "Send SMS"],
    ["call", "Call"],
    ["camera", "Photo"],
    ["key", "OTP reveal"],
  ];
  return (
    <Reveal
      at={at}
      out={out}
      style={{
        position: "absolute",
        left: 0,
        right: 0,
        top: 230,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 40 }}>
        <Counter to={4} at={at} style={display(300, { lineHeight: 0.85 })} />
        <div style={display(92, { lineHeight: 1 })}>
          actions always
          <br />
          <span style={{ color: C.blueText }}>ask first.</span>
        </div>
      </div>
      <div style={{ display: "flex", gap: 28, marginTop: 70 }}>
        {items.map(([icon, label], i) => {
          const s = at + 20 + i * 3;
          const p = interpolate(frame, [s, s + 12], [0, 1], {
            ...clamp,
            easing: EXPO,
          });
          const lock = interpolate(frame, [s + 8, s + 16], [0, 1], {
            ...clamp,
            easing: EXPO,
          });
          return (
            <div
              key={label}
              style={{
                width: 250,
                padding: "26px 0 22px",
                borderRadius: 24,
                background: "rgba(18,19,28,.9)",
                border: `1px solid rgba(139,147,255,${0.2 + 0.5 * lock})`,
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                gap: 14,
                color: C.paper,
                opacity: p,
                translate: `0 ${(1 - p) * 30}px`,
                position: "relative",
              }}
            >
              <Icon name={icon} size={52} stroke={1.5} />
              <div style={mono(17, { color: C.paper })}>{label}</div>
              <div
                style={{
                  position: "absolute",
                  right: -12,
                  top: -12,
                  width: 42,
                  height: 42,
                  borderRadius: 21,
                  background: C.blue,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  scale: `${lock}`,
                  boxShadow: "0 0 24px rgba(31,43,255,.7)",
                }}
              >
                <Icon name="lock" size={22} color={C.paper} stroke={2} />
              </div>
            </div>
          );
        })}
      </div>
    </Reveal>
  );
};

/** Privacy + project facts. */
const Facts: React.FC<{ at: number }> = ({ at }) => {
  const frame = useCurrentFrame();
  const end = interpolate(frame, [586, 600], [0, 1], {
    ...clamp,
    easing: EASE_IN,
  });
  const tiles: { n: number; label: string; accent?: boolean }[] = [
    { n: 0, label: "Third-party services", accent: true },
    { n: 0, label: "Telemetry", accent: true },
    { n: TOOLS, label: "Tools" },
    { n: TESTS, label: "Tests" },
  ];
  return (
    <AbsoluteFill style={{ opacity: 1 - end, scale: `${1 - end * 0.1}` }}>
      <Headline
        top={190}
        text="Talks only to his phone."
        start={at}
        stagger={2}
        size={100}
        accent={["only"]}
      />
      <Tag
        at={at + 6}
        style={{
          left: 0,
          right: 0,
          top: 340,
          textAlign: "center",
          color: C.mist,
        }}
      >
        OTP codes stay hidden by default
      </Tag>
      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          top: 470,
          display: "flex",
          justifyContent: "center",
          gap: 28,
        }}
      >
        {tiles.map((t, i) => {
          const s = at + 10 + i * 4;
          const p = interpolate(frame, [s, s + 14], [0, 1], {
            ...clamp,
            easing: EXPO,
          });
          return (
            <div
              key={t.label}
              style={{
                width: 360,
                height: 250,
                borderRadius: 28,
                padding: "30px 34px",
                background: t.accent
                  ? "rgba(31,43,255,.16)"
                  : "rgba(18,19,28,.85)",
                border: `1px solid ${t.accent ? "rgba(139,147,255,.5)" : "rgba(255,255,255,.14)"}`,
                display: "flex",
                flexDirection: "column",
                justifyContent: "space-between",
                opacity: p,
                translate: `0 ${(1 - p) * 40}px`,
              }}
            >
              <Counter
                to={t.n}
                at={s}
                style={display(130, {
                  color: t.accent ? C.blueText : C.paper,
                  lineHeight: 0.9,
                })}
              />
              <div style={mono(17, { color: C.paper })}>{t.label}</div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

export const Impact: React.FC = () => {
  const cue = useCues(ID);
  const i1 = cue("i1");
  const i2 = cue("i2");
  const i3 = cue("i3");
  const i4 = cue("i4");
  const i5 = cue("i5");
  return (
    <AbsoluteFill style={{ backgroundColor: C.ink }}>
      <FilmField sectionId={ID} intensity={0.7} />
      <Split at={i1.s} nowAt={i2.s - 4} out={i3.s - 10} />

      <Headline
        top={180}
        text="Reads Android, not pixels."
        start={i3.s}
        stagger={2}
        size={104}
        accent={["Android"]}
        exitAt={i4.s - 10}
      />
      <Drift from={i3.s} to={i4.s}>
        <Steps at={i3.s + 6} out={i4.s - 10} />
      </Drift>
      <Tag
        at={i3.s + 40}
        out={i4.s - 10}
        style={{
          left: 0,
          right: 0,
          top: 820,
          textAlign: "center",
          color: C.mist,
        }}
      >
        Mean agent steps per task · CLI-Advantage Suite
      </Tag>
      <SourceLine at={i3.s + 8} out={i4.s - 6}>
        Gu et al., 2026, arXiv 2606.19388 · the study&apos;s finding about
        command-line vs screen agents, not a test of Phone Senses
      </SourceLine>

      <Gated at={i4.s} out={i5.s - 10} />
      <Drift from={i5.s} to={600} amount={0.03}>
        <Facts at={i5.s} />
      </Drift>
    </AbsoluteFill>
  );
};
