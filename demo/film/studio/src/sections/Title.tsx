import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { C, EASE_IN, EXPO, Kinetic, Mark, Wordmark } from "../brand";
import { clamp, FilmField, mono, Tag, useCues } from "../motion";

const ID = "title";
const MARK = 220;
const WORD = 150;
const GAP = 44;
const WORD_W = 1122; // measured width of the 150 px wordmark
const SHIFT = (WORD_W + GAP) / 2;

/** "His agent knew none of it." slams in (104 % -> 100 %) with an empty prompt blinking under it. */
const AgentLine: React.FC<{ at: number; out: number }> = ({ at, out }) => {
  const frame = useCurrentFrame();
  const blink = Math.floor((frame - at) / 9) % 2 === 0;
  const o = interpolate(frame, [out, out + 8], [1, 0], {
    ...clamp,
    easing: EASE_IN,
  });
  return (
    <AbsoluteFill
      style={{
        alignItems: "center",
        justifyContent: "center",
        flexDirection: "column",
        gap: 36,
      }}
    >
      <div
        style={{
          scale: `${interpolate(frame, [at + 6, at + 15], [1.04, 1], { ...clamp, easing: EXPO })}`,
        }}
      >
        <Kinetic
          text="His agent knew none of it."
          start={at}
          stagger={2}
          size={120}
          maxWidth={1728}
          exitAt={out}
        />
      </div>
      <div
        style={{
          ...mono(26, {
            color: C.mist,
            letterSpacing: "0.04em",
            textTransform: "none",
          }),
          opacity: interpolate(frame, [at + 10, at + 20], [0, 1], clamp) * o,
        }}
      >
        hermes&nbsp;&gt;&nbsp;<span style={{ opacity: blink ? 1 : 0 }}>▌</span>
      </div>
    </AbsoluteFill>
  );
};

/** Mark assembles, the sensing pixel lands last with a flash, then the lockup forms with the wordmark. */
const Reveal: React.FC<{ markAt: number; now: number; wordAt: number }> = ({
  markAt,
  now,
  wordAt,
}) => {
  const frame = useCurrentFrame();
  const move = interpolate(frame, [wordAt - 4, wordAt + 14], [0, 1], {
    ...clamp,
    easing: EXPO,
  });
  const flash = interpolate(frame, [now, now + 3, now + 16], [0, 1, 0], clamp);
  const ring = interpolate(frame, [now, now + 18], [0, 1], {
    ...clamp,
    easing: EXPO,
  });
  const end = interpolate(frame, [228, 240], [0, 1], {
    ...clamp,
    easing: EASE_IN,
  });
  // sensing-pixel centre relative to the mark's centre
  const px = (27 / 64) * MARK;
  const py = (-29 / 64) * MARK;
  return (
    <AbsoluteFill
      style={{
        alignItems: "center",
        justifyContent: "center",
        opacity: 1 - end,
        filter: end > 0 ? `blur(${end * 10}px)` : undefined,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: GAP }}>
        <div
          style={{
            position: "relative",
            width: MARK,
            height: MARK,
            translate: `${(1 - move) * SHIFT}px 0`,
          }}
        >
          <Mark size={MARK} start={markAt} />
          <div
            style={{
              position: "absolute",
              left: MARK / 2 + px - 120,
              top: MARK / 2 + py - 120,
              width: 240,
              height: 240,
              borderRadius: 240,
              background: `radial-gradient(circle, rgba(139,147,255,${0.95 * flash}) 0%, rgba(31,43,255,${0.6 * flash}) 22%, transparent 62%)`,
            }}
          />
          <div
            style={{
              position: "absolute",
              left: MARK / 2 + px,
              top: MARK / 2 + py,
              width: 16 + ring * 180,
              height: 16 + ring * 180,
              translate: "-50% -50%",
              borderRadius: 999,
              border: `2px solid rgba(139,147,255,${(1 - ring) * 0.9})`,
              opacity: frame >= now ? 1 : 0,
            }}
          />
        </div>
        <div
          style={{
            width: WORD_W,
            whiteSpace: "nowrap",
            opacity: frame >= wordAt ? 1 : 0,
          }}
        >
          <Wordmark size={WORD} start={wordAt} />
        </div>
      </div>
    </AbsoluteFill>
  );
};

export const Title: React.FC = () => {
  const cue = useCues(ID);
  const t1 = cue("t1");
  const t2 = cue("t2");
  const t3 = cue("t3");
  const now = t3.s + 12; // the word "now"
  return (
    <AbsoluteFill style={{ backgroundColor: C.ink }}>
      <FilmField sectionId={ID} intensity={0.75} />
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
        <Kinetic
          text="His phone knew all of it."
          start={t1.s}
          stagger={2}
          size={120}
          maxWidth={1728}
          exitAt={t2.s - 8}
        />
      </AbsoluteFill>
      <AgentLine at={t2.s} out={t3.s - 22} />
      <Reveal markAt={now - 26} now={now} wordAt={t3.e + 6} />
      <AbsoluteFill
        style={{
          alignItems: "center",
          justifyContent: "center",
          translate: "0 210px",
        }}
      >
        <Kinetic
          text="Until now."
          start={t3.s - 2}
          stagger={3}
          size={72}
          exitAt={t3.e + 2}
        />
      </AbsoluteFill>
      <Tag
        at={t3.e + 26}
        out={226}
        style={{
          left: 0,
          right: 0,
          top: 690,
          textAlign: "center",
          color: C.mist,
        }}
      >
        A plugin for Hermes Agent
      </Tag>
    </AbsoluteFill>
  );
};
