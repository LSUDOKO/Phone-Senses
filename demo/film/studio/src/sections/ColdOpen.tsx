import React from "react";
import { AbsoluteFill, interpolate, random, useCurrentFrame } from "remotion";
import { C, DISPLAY, EASE_IN, EXPO, Kinetic } from "../brand";
import {
  clamp,
  DipOut,
  FilmField,
  Glitch,
  Icon,
  mono,
  NOTIFS,
  NotifCard,
  Tag,
  useCues,
  useShake,
} from "../motion";

const ID = "cold";
const PILE = 28;

/** Notification cards piling up, faster and faster, slightly askew. */
const Pile: React.FC<{ dimAt: number; outAt: number }> = ({ dimAt, outAt }) => {
  const frame = useCurrentFrame();
  const dim = interpolate(frame, [dimAt, dimAt + 12], [0, 1], {
    ...clamp,
    easing: EXPO,
  });
  const out = interpolate(frame, [outAt, outAt + 6], [0, 1], {
    ...clamp,
    easing: EASE_IN,
  });
  const shake = useShake(52, 62, 6, "pile");
  return (
    <AbsoluteFill
      style={{
        opacity: (1 - dim * 0.72) * (1 - out),
        filter: dim > 0 ? `blur(${dim * 7}px)` : undefined,
        scale: `${interpolate(frame, [0, 80], [1, 1.07], clamp) - dim * 0.06}`,
        translate: shake,
      }}
    >
      {Array.from({ length: PILE }).map((_, i) => {
        const at = Math.round(2 + 66 * Math.pow(i / PILE, 0.75));
        const p = interpolate(frame, [at, at + 10], [0, 1], {
          ...clamp,
          easing: EXPO,
        });
        if (p <= 0) return null;
        const x = (random(`px${i}`) - 0.5) * 1280;
        const y = (random(`py${i}`) - 0.5) * 700 - 50;
        const rot = (random(`pr${i}`) - 0.5) * 16;
        // older cards sink back as new ones land
        const age = interpolate(frame, [at + 10, at + 60], [0, 1], clamp);
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: 960 - 260 + x,
              top: 540 - 60 + y,
              opacity: p * (1 - age * 0.35),
              translate: `0 ${(1 - p) * 260}px`,
              rotate: `${rot * p}deg`,
              scale: `${1.24 - 0.1 * p - age * 0.06}`,
            }}
          >
            <NotifCard n={NOTIFS[i % NOTIFS.length]} />
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

/** The fake scam SMS, large, with "BLOCKED" glitching. */
const ScamCard: React.FC<{ at: number; glitchAt: number; outAt: number }> = ({
  at,
  glitchAt,
  outAt,
}) => {
  const frame = useCurrentFrame();
  const p = interpolate(frame, [at, at + 14], [0, 1], {
    ...clamp,
    easing: EXPO,
  });
  const out = interpolate(frame, [outAt, outAt + 5], [0, 1], {
    ...clamp,
    easing: EASE_IN,
  });
  const shake = useShake(glitchAt, glitchAt + 8, 10, "scam");
  const shake2 = useShake(outAt - 10, outAt, 14, "scam2");
  const g =
    (frame >= glitchAt && frame <= glitchAt + 6) ||
    (frame >= outAt - 10 && frame <= outAt);
  const split = g ? 6 + random(`bs${frame}`) * 8 : 0;
  return (
    <AbsoluteFill
      style={{
        alignItems: "center",
        justifyContent: "center",
        opacity: p * (1 - out),
      }}
    >
      <Glitch
        windows={[
          [glitchAt, glitchAt + 5],
          [outAt - 10, outAt],
        ]}
        seed="scamcard"
        amp={16}
      >
        <div
          style={{
            width: 1180,
            padding: "40px 48px 44px",
            borderRadius: 34,
            background: "rgba(24,25,33,.94)",
            border: "1px solid rgba(255,255,255,.14)",
            boxShadow:
              "0 50px 140px rgba(0,0,0,.7), inset 0 1px 0 rgba(255,255,255,.1)",
            translate: `${shake === "0px 0px" ? shake2 : shake}`,
            scale: `${1.06 - 0.06 * p}`,
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 18,
              ...mono(18, { letterSpacing: "0.08em" }),
            }}
          >
            <div
              style={{
                width: 52,
                height: 52,
                borderRadius: 14,
                background: "rgba(255,255,255,.08)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: C.paper,
              }}
            >
              <Icon name="sms" size={30} />
            </div>
            <span style={{ color: C.paper }}>Messages · VM-ALERTZ</span>
            <span style={{ marginLeft: "auto" }}>now</span>
          </div>
          <div
            style={{
              fontFamily: DISPLAY,
              fontWeight: 500,
              fontSize: 50,
              lineHeight: 1.22,
              color: C.paper,
              marginTop: 28,
              letterSpacing: "-0.01em",
            }}
          >
            Dear customer, your bank account will be{" "}
            <span
              style={{
                fontWeight: 800,
                fontStretch: "115%",
                display: "inline-block",
                textShadow: split
                  ? `${split}px 0 ${C.blue}, ${-split}px 0 rgba(154,160,180,.85)`
                  : undefined,
                translate: g
                  ? `${(random(`bx${frame}`) - 0.5) * 18}px 0`
                  : undefined,
              }}
            >
              BLOCKED
            </span>{" "}
            today. Update KYC now:{" "}
            <span
              style={{
                whiteSpace: "nowrap",
                textDecoration: "underline",
                textDecorationColor: "rgba(241,241,238,.4)",
                color: "rgba(241,241,238,.8)",
              }}
            >
              bnk-kyc-•••.co
            </span>
          </div>
        </div>
      </Glitch>
    </AbsoluteFill>
  );
};

/** "Exam week." with tracking tightening during the hold. */
const ExamWeek: React.FC<{ at: number; outAt: number }> = ({ at, outAt }) => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
      <div
        style={{
          scale: `${interpolate(frame, [at, outAt + 8], [1.03, 0.985], clamp)}`,
        }}
      >
        <Kinetic
          text="Exam week."
          start={at}
          stagger={2}
          size={200}
          exitAt={outAt}
        />
      </div>
    </AbsoluteFill>
  );
};

export const ColdOpen: React.FC = () => {
  const cue = useCues(ID);
  const c2 = cue("c2");
  const c3 = cue("c3");
  const cardOut = c3.s - 12;
  return (
    <AbsoluteFill style={{ backgroundColor: C.ink }}>
      <FilmField sectionId={ID} intensity={0.55} />
      <Pile dimAt={c2.s - 6} outAt={cardOut} />
      <Tag at={4} out={cardOut} style={{ left: 96, top: 64 }}>
        Hamirpur · exam week · 07:42
      </Tag>
      <ScamCard at={c2.s - 4} glitchAt={c2.e - 16} outAt={cardOut} />
      <Tag
        at={c2.s + 6}
        out={cardOut}
        style={{ right: 96, top: 64, textAlign: "right" }}
      >
        Scam text · re-created
      </Tag>
      <ExamWeek at={c3.s - 2} outAt={286} />
      <DipOut at={296} />
    </AbsoluteFill>
  );
};
